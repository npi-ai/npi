package reconcile

import (
	"context"
	"errors"
	"time"

	"github.com/npi-ai/npi/server/api"
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

type Controller[R Resource] interface {
	Start(ctx context.Context) error
}

type BaseController[R Resource] struct {
	name          string
	maxGoroutines int
}

func (c *BaseController[Resource]) SetName(name string) {
	c.name = name
}

func (c *BaseController[Resource]) SetMaximumParallelism(max int) {
	c.maxGoroutines = max
}

func (c *BaseController[Resource]) GetMaximumParallelism() int {
	if c.maxGoroutines == 0 {
		return 64
	}
	return c.maxGoroutines
}

func (c *BaseController[Resource]) Reconcile(
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
				Sort: bson.M{"scheduled_at": 1},
			}
			result := coll.FindOneAndUpdate(ctx,
				bson.M{"status": sourceState, "retry_at": bson.M{"$lte": time.Now()}},
				bson.M{"$set": bson.M{
					"status":      midState,
					"updated_at":  time.Now(),
					"in_progress": true,
				}},
				&opts,
			)
			if result.Err() != nil {
				if !errors.Is(result.Err(), mongo.ErrNoDocuments) {
					log.Error(ctx).Err(result.Err()).
						Str("status", string(sourceState)).
						Str("resource", c.name).
						Msg("failed to get object from database")
					time.Sleep(10 * time.Second)
				}
				time.Sleep(time.Second)
				continue
			}
			R := g()
			err := result.Decode(&R)
			if err != nil {
				row, _err := result.Raw()
				// TODO update error
				log.Error(ctx).
					Err(err).
					Str("status", string(sourceState)).
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
					Str("status", string(sourceState)).
					Str("resource", c.name).
					Msg("start to process the resource")
				if err = f(ctx, r); err != nil {
					if api.IsError(err, api.ErrResourceRetry) {
						log.Info(ctx).
							Str("resource_id", r.ObjectID().Hex()).
							Str("status", string(sourceState)).
							Str("resource", c.name).
							Msg("the resource is not ready")
						_, err = coll.UpdateOne(ctx,
							bson.M{"_id": r.ObjectID()},
							bson.M{"$set": bson.M{
								"updated_at":  time.Now(),
								"retry_at":    time.Now().Add(10 * time.Second),
								"retry_times": r.RetryTimes() + 1,
								"status":      sourceState,
								"in_progress": false,
							}},
						)
						if err != nil {
							log.Error(ctx).Err(err).
								Str("resource_id", r.ObjectID().Hex()).
								Str("status", string(sourceState)).
								Str("resource", c.name).
								Interface("resource", r).
								Int("retry_times", r.RetryTimes()).
								Msg("failed to update status")
						}
						return
					}
					log.Warn(ctx).Err(err).
						Str("resource_id", id.Hex()).
						Str("status", string(sourceState)).
						Str("resource", c.name).
						Msg("failed to handle status")
					_, err = coll.UpdateOne(ctx,
						bson.M{"_id": id},
						bson.M{"$set": bson.M{
							"updated_at":  time.Now(),
							"status":      model.ResourceStatusError,
							"error":       err.Error(),
							"in_progress": false,
						}},
					)
					if err != nil {
						log.Error(ctx).Err(err).
							Str("resource_id", id.Hex()).
							Str("status", string(sourceState)).
							Str("resource", c.name).
							Interface("resource", r).
							Msg("failed to update status")
					}
				} else {
					log.Info(ctx).
						Str("resource_id", id.Hex()).
						Str("before", string(sourceState)).
						Str("after", string(targetState)).
						Str("resource", c.name).
						Dur("duration", time.Since(start)).
						Msg("the resource is handled successfully")
					_, err = coll.UpdateOne(ctx,
						bson.M{"_id": id},
						bson.M{"$set": bson.M{
							"updated_at":  time.Now(),
							"status":      targetState,
							"in_progress": false,
						}},
					)
					if err != nil {
						log.Warn(ctx).
							Str("resource_id", id.Hex()).
							Str("before", string(sourceState)).
							Str("after", string(targetState)).
							Str("resource", c.name).
							Dur("duration", time.Since(start)).
							Msg("failed to update database")
					}
				}
			}(R)
		}
	}
}
