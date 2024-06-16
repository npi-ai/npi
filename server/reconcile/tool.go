package reconcile

import (
	"context"
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/log"
	"github.com/npi-ai/npi/server/model"
	"github.com/npi-ai/npi/server/service"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
)

// state transition:
//
// draft -> queued -> deploying -> running -> delete_marked -> deleting -> deleted
// running -> pause_marked -> pausing -> paused
// deploying/running/deleting/pausing -> error
type toolReconciler struct {
	BaseReconciler[model.ToolInstance]
	coll       *mongo.Collection
	builderSvc *service.BuilderService
}

func NewToolReconciler() Reconciler[model.ToolInstance] {
	return &toolReconciler{
		coll: db.GetCollection(db.CollToolInstances),
		builderSvc: service.NewBuilderService(
			"992297059634.dkr.ecr.us-west-2.amazonaws.com",
			"npiai-tools-build-test",
			"/Users/wenfeng/tmp/build",
			"/Users/wenfeng/workspace/npi-ai/npi/server/scripts/tool_helper.py",
		),
	}
}

func (tc *toolReconciler) Start(ctx context.Context) error {
	tc.BaseReconciler.SetName("Tool")
	g := func() model.ToolInstance {
		return model.ToolInstance{}
	}

	// recover tools in progress
	result, err := tc.coll.UpdateMany(ctx,
		bson.M{
			"in_progress": true,
		},
		[]bson.M{
			{"$set": bson.M{
				"current_state": "$source_state",
				"in_progress":   false,
			}},
		})
	if err != nil {
		return db.ConvertError(err)
	}
	log.Info().Int("recovered", int(result.ModifiedCount)).Msg("tool recovered")
	go tc.Reconcile(ctx, tc.coll,
		model.ResourceStatusCreated,
		model.ResourceStatusBuilding,
		model.ResourceStatusBuilt,
		g, tc.BuildingHandler)

	go tc.Reconcile(ctx, tc.coll,
		model.ResourceStatusQueued,
		model.ResourceStatusDeploying,
		model.ResourceStatusRunning,
		g, tc.DeployingHandler)

	go tc.Reconcile(ctx, tc.coll,
		model.ResourceStatusDeleteMarked,
		model.ResourceStatusDeleting,
		model.ResourceStatusDeleted,
		g, tc.DeletingHandler)

	go tc.Reconcile(ctx, tc.coll,
		model.ResourceStatusPauseMarked,
		model.ResourceStatusPausing,
		model.ResourceStatusPaused,
		g, tc.PausingHandler)
	return nil
}

func (tc *toolReconciler) BuildingHandler(ctx context.Context, ws model.ToolInstance) error {
	if err := tc.builderSvc.Build(ctx, ws.Metadata); err != nil {
		return err
	}
	return nil
}

func (tc *toolReconciler) DeployingHandler(ctx context.Context, ws model.ToolInstance) error {
	println("deploying")
	return nil
}

func (tc *toolReconciler) DeletingHandler(ctx context.Context, ws model.ToolInstance) error {
	println("deleting")
	return nil
}

func (tc *toolReconciler) PausingHandler(ctx context.Context, ws model.ToolInstance) error {
	println("pausing")
	return nil
}
