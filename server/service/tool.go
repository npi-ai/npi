package service

import (
	"context"
	"fmt"
	"github.com/gin-gonic/gin"
	"time"

	"github.com/npi-ai/npi/server/api"
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/log"
	"github.com/npi-ai/npi/server/model"
	"github.com/npi-ai/npi/server/utils"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
)

type ToolService struct {
	toolColl          *mongo.Collection
	toolInstancesColl *mongo.Collection
	apiKeyColl        *mongo.Collection
	s3                *db.S3
	s3Bucket          string
	toolEndpointRoot  string
	appSvc            *AppService
}

func NewTool(toolAccessPoint string, cfg db.S3Config) *ToolService {
	return &ToolService{
		toolColl:          db.GetCollection(db.CollTools),
		toolInstancesColl: db.GetCollection(db.CollToolInstances),
		apiKeyColl:        db.GetCollection(db.CollAPIKey),
		s3:                db.GetAWSS3(cfg),
		s3Bucket:          cfg.Bucket,
		toolEndpointRoot:  toolAccessPoint,
	}
}

func (ctrl *ToolService) ListTool(ctx context.Context, tenantID primitive.ObjectID) ([]model.Tool, error) {
	cursor, err := ctrl.toolColl.Find(ctx, bson.M{"tenant_id": tenantID})
	if err != nil {
		log.Warn(ctx).Err(err).Msg("Failed to list tools")
		return nil, db.ConvertError(err)
	}
	tools := make([]model.Tool, 0)
	if err = cursor.All(ctx, &tools); err != nil {
		log.Warn(ctx).Err(err).Msg("Failed to decode tools")
		return nil, db.ConvertError(err)
	}
	return tools, nil
}

func (ctrl *ToolService) CreateTool(ctx context.Context, tenantID primitive.ObjectID, req *api.ToolRequest, data []byte) (*model.Tool, error) {
	tool := &model.Tool{
		Base:       model.NewBase(ctx),
		Name:       req.Name,
		TenantID:   tenantID,
		AuthMethod: model.AuthNone,
	}

	if tool.Name == "" {
		tool.Name = "Untitled Tool"
	}

	toolInstance := &model.ToolInstance{
		BaseResource: model.NewBaseResource(ctx),
		ToolID:       tool.ID,
		TenantID:     tool.TenantID,
		Version:      time.Now().Format("20060102150405"),
		Metadata: model.ToolMetadata{
			Name:        tool.Name,
			Description: "NPi Tools",
			Authors:     []string{tool.CreatedBy},
		},
	}
	toolInstance.Metadata.ID = toolInstance.ID.Hex()
	toolInstance.CurrentState = model.ResourceStatusCreated
	toolInstance.SourceState = model.ResourceStatusCreated
	toolInstance.TargetState = model.ResourceStatusBuilt
	tool.HeadVersionID = toolInstance.ID

	s3ObjectID := fmt.Sprintf("%s/source.zip", toolInstance.ID.Hex())
	if err := ctrl.s3.PutObject(ctx, s3ObjectID, ctrl.s3Bucket, data); err != nil {
		log.Warn(ctx).Err(err).Msg("Failed to upload file to S3")
		return nil, api.ErrInternal.WithMessage("Failed to upload file to S3")
	}
	toolInstance.S3URI = fmt.Sprintf("s3://%s/%s", ctrl.s3Bucket, s3ObjectID)

	if _, err := ctrl.toolColl.InsertOne(ctx, tool); err != nil {
		log.Warn(ctx).Err(err).Msg("Failed to save Tool to database")
		return nil, db.ConvertError(err)
	}

	if _, err := ctrl.toolInstancesColl.InsertOne(ctx, toolInstance); err != nil {
		log.Warn(ctx).Err(err).Msg("Failed to save ToolInstance to database")
		return nil, db.ConvertError(err)
	}
	return tool, nil
}

func (ctrl *ToolService) PublishTool(ctx context.Context, toolID primitive.ObjectID) error {
	tool, err := ctrl.getToolByID(ctx, toolID)
	if err != nil {
		return err
	}
	instance, err := ctrl.getToolInstanceByID(ctx, tool.HeadVersionID)
	if err != nil {
		log.Warn(ctx).Err(err).Msg("Failed to get tool instance")
		return err
	}
	if instance.CurrentState != model.ResourceStatusBuilt {
		return api.ErrInvalidRequest.WithMessage("invalid state, tool state of [ Built ] is required")
	}

	_, err = ctrl.toolInstancesColl.UpdateOne(ctx,
		bson.M{"_id": instance.ID},
		bson.M{
			"$set": bson.M{
				"current_state": model.ResourceStatusQueued,
				"source_state":  model.ResourceStatusQueued,
				"target_state":  model.ResourceStatusRunning,
				"state_history": append(instance.StateHistory, instance.CurrentState),
				"updated_at":    time.Now(),
				"updated_by":    utils.GetUserID(ctx),
			},
		})
	if err != nil {
		log.Warn(ctx).Err(err).Msg("Failed to update tool instance")
		return db.ConvertError(err)
	}
	return nil
}

func (ctrl *ToolService) GetToolOverview(ctx context.Context, toolID primitive.ObjectID) (api.ToolSummary, error) {
	tool, err := ctrl.getToolByID(ctx, toolID)
	if err != nil {
		return api.ToolSummary{}, err
	}

	instance, err := ctrl.getToolInstanceByID(ctx, tool.HeadVersionID)
	if err != nil {
		return api.ToolSummary{}, err
	}
	summary := api.ToolSummary{
		ID:           tool.ID.Hex(),
		Name:         instance.Metadata.Name,
		Status:       string(instance.CurrentState),
		Description:  instance.Metadata.Description,
		Runtime:      instance.FunctionSpec.Runtime,
		Dependencies: instance.FunctionSpec.Dependencies,
		Endpoint:     fmt.Sprintf("%s/%s", ctrl.toolEndpointRoot, tool.ID.Hex()),
	}
	summary.Runtime.Image = instance.Image

	app, err := ctrl.appSvc.GetAppClient(tool.AppClientID)
	if err != nil {
		return api.ToolSummary{}, err
	}

	summary.Authentication.Type = tool.AuthMethod
	if !tool.APIKeyID.IsZero() {
		key, err := ctrl.GetAPIKey(ctx, tool.APIKeyID)
		if err != nil {
			return api.ToolSummary{}, err
		}
		apiKey := ""
		for idx := 0; idx < len(key.Value)-4; idx++ {
			apiKey += "*"
		}
		summary.Authentication.APIKeyLast4 = key.Value[len(key.Value)-4:]
	}
	summary.Authentication.ClientID = app.ClientID

	return summary, nil
}

func (ctrl *ToolService) GetAPIKey(ctx context.Context, keyID primitive.ObjectID) (model.APIKey, error) {
	result := ctrl.apiKeyColl.FindOne(ctx, bson.M{"_id": keyID})
	if result.Err() != nil {
		return model.APIKey{}, db.ConvertError(result.Err())
	}
	apiKey := model.APIKey{}
	if err := result.Decode(&apiKey); err != nil {
		return model.APIKey{}, db.ConvertError(err)
	}

	return apiKey, nil
}

func (ctrl *ToolService) GetToolFunction(ctx context.Context, toolID primitive.ObjectID) ([]model.Function, error) {
	instance, err := ctrl.getToolInstanceByCtx(ctx, toolID)
	if err != nil {
		return nil, err
	}
	return instance.FunctionSpec.Functions, nil
}

func (ctrl *ToolService) DeleteTool(ctx context.Context, toolID primitive.ObjectID) error {
	tool, err := ctrl.getToolByID(ctx, toolID)
	if err != nil {
		return err
	}

	_, err = ctrl.toolColl.DeleteOne(ctx, bson.M{"_id": tool.ID})
	if err != nil {
		return db.ConvertError(err)
	}

	_, err = ctrl.toolInstancesColl.UpdateMany(ctx,
		bson.M{"tool_id": tool.ID},
		bson.M{
			"$set": bson.M{
				"current_state": model.ResourceStatusDeleteMarked,
				"source_state":  model.ResourceStatusDeleteMarked,
				"target_state":  model.ResourceStatusDeleted,
				"updated_at":    time.Now(),
				"updated_by":    utils.GetUserID(ctx),
			},
		},
	)
	if err != nil {
		return db.ConvertError(err)
	}
	return nil
}

func (ctrl *ToolService) CreateToolVersion(ctx context.Context) {

}

func (ctrl *ToolService) GetToolOpenAISchema(ctx context.Context, toolID primitive.ObjectID) ([]byte, error) {
	tool, err := ctrl.getToolByID(ctx, toolID)
	if err != nil {
		return nil, err
	}
	instance, err := ctrl.getToolInstanceByID(ctx, tool.HeadVersionID)
	if err != nil {
		return nil, err
	}
	return instance.OpenAISchema(), nil
}

// GetToolOpenAPISchema https://api.npi.ai/schemas/{tool_id}
func (ctrl *ToolService) GetToolOpenAPISchema(ctx context.Context, toolID primitive.ObjectID) ([]byte, error) {
	tool, err := ctrl.getToolByID(ctx, toolID)
	if err != nil {
		return nil, err
	}
	instance, err := ctrl.getToolInstanceByID(ctx, tool.HeadVersionID)
	if err != nil {
		return nil, err
	}
	return instance.OpenAISchema(), nil
}

func (ctrl *ToolService) getToolByID(ctx context.Context, toolID primitive.ObjectID) (*model.Tool, error) {
	result := ctrl.toolColl.FindOne(ctx, bson.M{"_id": toolID})
	if result.Err() != nil {
		return nil, db.ConvertError(result.Err())
	}
	tool := &model.Tool{}
	_ = result.Decode(&tool)
	return tool, nil
}

func (ctrl *ToolService) getToolInstanceByCtx(ctx context.Context, toolID primitive.ObjectID) (*model.ToolInstance, error) {
	tool, err := ctrl.getToolByID(ctx, toolID)
	if err != nil {
		return nil, err
	}

	return ctrl.getToolInstanceByID(ctx, tool.HeadVersionID)
}

func (ctrl *ToolService) getToolInstanceByID(ctx context.Context, id primitive.ObjectID) (*model.ToolInstance, error) {
	result := ctrl.toolInstancesColl.FindOne(ctx, bson.M{"_id": id})
	if result.Err() != nil {
		return nil, db.ConvertError(result.Err())
	}
	tool := &model.ToolInstance{}
	_ = result.Decode(&tool)
	return tool, nil
}

func (ctrl *ToolService) GenerateAPIKey(c *gin.Context, id primitive.ObjectID) (string, error) {
	tool, err := ctrl.getToolByID(c, id)
	if err != nil {
		return "", err
	}

	var key model.APIKey
	if tool.APIKeyID.IsZero() {
		key = model.APIKey{
			Base:     model.NewBase(c),
			Value:    "npi-" + utils.GenerateRandomString(64, true, true, false),
			Provider: model.APIKeyProviderBuiltin,
		}
		if _, err = ctrl.apiKeyColl.InsertOne(c, key); err != nil {
			return "", db.ConvertError(err)
		}
		_, err = ctrl.toolColl.UpdateByID(c, id, bson.M{"$set": bson.M{"api_key_id": key.ID}})
		if err != nil {
			return "", db.ConvertError(err)
		}
	} else {
		key, err = ctrl.GetAPIKey(c, tool.APIKeyID)
		if err != nil {
			return "", err
		}
		key.Value = "npi-" + utils.GenerateRandomString(64, true, true, false)

		_, err = ctrl.apiKeyColl.UpdateByID(c,
			key.ID,
			bson.M{
				"$set": bson.M{
					"value":      key.Value,
					"updated_at": time.Now(),
					"updated_by": utils.GetUserID(c),
				},
			},
		)
		if err != nil {
			return "", db.ConvertError(err)
		}
	}
	return key.Value, nil
}

func (ctrl *ToolService) UpdateAuth(ctx context.Context, id primitive.ObjectID, method model.AuthType, clientID string) error {
	query := bson.M{
		"auth_method": method,
		"updated_by":  utils.GetUserID(ctx),
		"updated_at":  time.Now(),
	}

	if method == model.AuthOAuth {
		query["app_client_id"] = clientID
	}
	_, err := ctrl.toolColl.UpdateByID(ctx, id, query)
	return db.ConvertError(err)

}
