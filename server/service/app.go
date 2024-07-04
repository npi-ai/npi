package service

import (
	"context"

	"github.com/npi-ai/npi/server/api"
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/model"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
)

type AppService struct {
	coll *mongo.Collection
}

func NewAppService() *AppService {
	return &AppService{
		coll: db.GetCollection(db.CollOrganizations),
	}
}

func (as *AppService) GetOrCreateOrgDefaultAppClient(ctx context.Context, id primitive.ObjectID) (model.AppClient, error) {
	result := as.coll.FindOne(ctx, bson.M{
		"org_id":      id,
		"org_default": true,
	})
	cli := model.AppClient{}
	if result.Err() != nil {
		err := db.ConvertError(result.Err())
		if !api.IsErrNotFound(err) {
			return cli, err
		}
		cli.Base = model.NewBase(ctx)
		cli.OrgDefault = true
		cli.OrgID = id
	} else {
		if err := result.Decode(&cli); err != nil {
			return cli, db.ConvertError(err)
		}
	}
	return cli, nil
}

func (as *AppService) GetAppClient(id primitive.ObjectID) (model.AppClient, error) {
	return model.AppClient{}, nil
}
