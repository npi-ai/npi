package reconcile

import (
	"context"
	"errors"
	"time"

	"github.com/npi-ai/npi/server/log"
	"github.com/npi-ai/npi/server/model"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type Resource interface {
	model.ToolInstance
	ObjectID() primitive.ObjectID
	RetryTimes() int
}

type Reconciler[R Resource] interface {
	Start(ctx context.Context) error
}

type BaseReconciler[R Resource] struct {
	name          string
	maxGoroutines int
}

func (c *BaseReconciler[Resource]) SetName(name string) {
	c.name = name
}

func (c *BaseReconciler[Resource]) SetMaximumParallelism(max int) {
	c.maxGoroutines = max
}

func (c *BaseReconciler[Resource]) GetMaximumParallelism() int {
	if c.maxGoroutines == 0 {
		return 64
	}
	return c.maxGoroutines
}

func (c *BaseReconciler[Resource]) Reconcile(
	ctx context.Context,
	coll *mongo.Collection,
	sourceState, midState, targetState model.ResourceStatus,
	g func() Resource,
	f func(ctx context.Context,
		resource Resource) error) {
	barrier := make(chan struct{}, c.GetMaximumParallelism())
	for {
		select {
		case <-ctx.Done():
			return
		default:
			opts := options.FindOneAndUpdateOptions{
				Sort: bson.M{"created_at": 1},
			}
			result := coll.FindOneAndUpdate(ctx,
				bson.M{
					"current_state": sourceState,
					"in_progress":   false,
				},
				bson.M{"$set": bson.M{
					"current_state": midState,
					"updated_at":    time.Now(),
					"in_progress":   true,
				}},
				&opts,
			)
			if result.Err() != nil {
				if !errors.Is(result.Err(), mongo.ErrNoDocuments) {
					log.Error(ctx).Err(result.Err()).
						Str("resource", c.name).
						Msg("failed to get object from database")
				}
				time.Sleep(time.Second)
				continue
			}
			R := g()
			err := result.Decode(&R)
			if err != nil {
				row, _err := result.Raw()
				log.Error(ctx).
					Err(err).
					Str("resource", c.name).
					Interface("row_err", _err).
					Stringer("resource", row).Msg("failed to decode resource")
				continue
			}

			barrier <- struct{}{}
			go func(r Resource) {
				defer func() {
					<-barrier
				}()
				id := r.ObjectID()
				start := time.Now()
				log.Info(ctx).
					Str("resource_id", id.Hex()).
					Str("source_state", string(sourceState)).
					Str("target_state", string(targetState)).
					Str("resource", c.name).
					Msg("start to process the resource")
				if err = f(ctx, r); err != nil {
					log.Warn(ctx).Err(err).
						Str("resource_id", id.Hex()).
						Str("current_state", string(midState)).
						Str("resource", c.name).
						Msg("failed to handle status")
					_, err = coll.UpdateOne(ctx,
						bson.M{"_id": id},
						bson.M{"$set": bson.M{
							"updated_at":    time.Now(),
							"current_state": model.ResourceStatusError,
							"error":         err.Error(),
							"in_progress":   false,
						}},
					)
					if err != nil {
						log.Error(ctx).Err(err).
							Str("resource_id", id.Hex()).
							Str("current_state", string(midState)).
							Str("resource", c.name).
							Interface("resource", r).
							Msg("failed to update status")
					}
				} else {
					log.Info(ctx).
						Str("resource_id", id.Hex()).
						Str("source_state", string(sourceState)).
						Str("target_state", string(targetState)).
						Str("resource", c.name).
						Dur("duration", time.Since(start)).
						Msg("the resource is handled successfully")
					_, err = coll.UpdateOne(ctx,
						bson.M{"_id": id},
						bson.M{"$set": bson.M{
							"updated_at":    time.Now(),
							"current_state": targetState,
							"in_progress":   false,
						}},
					)
					if err != nil {
						log.Warn(ctx).
							Str("resource_id", id.Hex()).
							Str("source_state", string(sourceState)).
							Str("target_state", string(targetState)).
							Str("resource", c.name).
							Dur("duration", time.Since(start)).
							Msg("failed to update database")
					}
				}
			}(R)
		}
	}
}
