package controller

import (
	"context"

	"github.com/npi-ai/npi/internal/db"
	server "github.com/npi-ai/npi/proto/go/api"
	"go.mongodb.org/mongo-driver/mongo"
	"google.golang.org/protobuf/types/known/emptypb"
)

type Controller struct {
	toolSpecColl     *mongo.Collection
	toolInstanceColl *mongo.Collection
	leader           bool
}

var (
	_ server.ControllerServer = (*Controller)(nil)
)

func NewController() *Controller {
	return &Controller{
		toolSpecColl:     db.GetCollection(db.CollToolSpec),
		toolInstanceColl: db.GetCollection(db.CollToolInstance),
	}
}

func (ctrl *Controller) Start(ctx context.Context) {
	// start grpc server
	ctrl.startRouter(ctx, 8080)
}

func (ctrl *Controller) Stop() {
	// stop grpc server
}

func (ctrl *Controller) RegisterTool(context.Context, *server.RegisterToolRequest) (*server.RegisterToolResponse, error) {
	return nil, nil
}

func (ctrl *Controller) UnregisterTool(context.Context, *emptypb.Empty) (*emptypb.Empty, error) {
	return nil, nil
}

func (ctrl *Controller) Heartbeat(context.Context, *emptypb.Empty) (*emptypb.Empty, error) {
	return nil, nil
}
