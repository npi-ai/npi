package resource

import (
	"context"
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/log"
	"github.com/npi-ai/npi/server/model"
	"github.com/npi-ai/npi/server/model/resource"
	"github.com/npi-ai/npi/server/reconcile"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
)

type toolController struct {
	reconcile.BaseController[resource.ToolResource]
	coll *mongo.Collection
}

func NewToolController() reconcile.Controller[resource.ToolResource] {
	return &toolController{
		coll: db.GetCollection(db.CollTools),
	}
}

func (pr *toolController) Start(ctx context.Context) error {
	pr.BaseController.SetName("Project")
	g := func() resource.ToolResource {
		return resource.ToolResource{}
	}
	result, err := pr.coll.UpdateMany(
		ctx,
		bson.M{"status": model.ResourceStatusProcessing},
		bson.M{"$set": bson.M{"status": model.ResourceStatusUpdated}},
	)
	if err != nil {
		return err
	}

	log.Info().Int("recovered", int(result.ModifiedCount)).Msg("tool recovered")
	go pr.Reconcile(ctx, pr.coll,
		model.ResourceStatusUpdated,
		model.ResourceStatusProcessing,
		model.ResourceStatusSuccess,
		g, pr.UpdatedHandler)
	return nil
}

func (pr *toolController) UpdatedHandler(ctx context.Context, ws resource.ToolResource) error {
	return nil
}

func (pr *toolController) DeletingHandler(ctx context.Context, ws resource.ToolResource) error {
	return nil
}
