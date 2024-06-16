package controller

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/render"
	"github.com/npi-ai/npi/server/api"
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/log"
	"github.com/npi-ai/npi/server/model"
	"github.com/npi-ai/npi/server/utils"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
)

type IController interface {
	RegisterRoute(parent *gin.RouterGroup) error
}

type ToolController struct {
	toolColl          *mongo.Collection
	toolInstancesColl *mongo.Collection
	s3                *db.S3
	s3Bucket          string
}

func NewTool(bucket string) IController {
	return &ToolController{
		toolColl:          db.GetCollection(db.CollTools),
		toolInstancesColl: db.GetCollection(db.CollToolInstances),
		s3:                db.GetS3(),
		s3Bucket:          bucket,
	}
}

func (ctrl *ToolController) RegisterRoute(parent *gin.RouterGroup) error {
	toolRouter := parent.Group("/tools")
	toolRouter.POST("", ctrl.CreateTool)
	toolRouter.DELETE("/:tool_id", ctrl.DeleteTool)
	toolRouter.POST("/:tool_id/publish", ctrl.PublishTool)
	toolRouter.GET("/:tool_id/openai", ctrl.GetToolOpenAISchema)
	toolRouter.GET("/:tool_id/openapi", ctrl.GetToolOpenAPISchema)
	return nil
}

func (ctrl *ToolController) CreateTool(ctx *gin.Context) {
	toolReq := &api.ToolRequest{}
	reqStr := ctx.PostForm("body")
	if reqStr == "" {
		api.ResponseWithError(ctx, api.ErrInvalidRequest.WithMessage("Empty request body"))
		return
	}
	if err := json.Unmarshal([]byte(reqStr), toolReq); err != nil {
		api.ResponseWithError(ctx, api.ErrInvalidRequest.WithMessage("Invalid request body"))
		return
	}
	if toolReq.From != api.ToolFromZip {
		api.ResponseWithError(ctx, api.ErrInvalidRequest.WithMessage("Only support zip file"))
		return
	}

	tool := &model.Tool{
		Base:  model.NewBase(ctx),
		Name:  toolReq.Name,
		OrgID: utils.GetOrgID(ctx),
	}

	if tool.Name == "" {
		tool.Name = utils.GenerateRandomString(8, false, false)
	}

	toolInstance := &model.ToolInstance{
		BaseResource: model.NewBaseResource(ctx),
		ToolID:       tool.ID,
		OrgID:        tool.OrgID,
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

	file, err := ctx.FormFile("tool")
	if err != nil {
		api.ResponseWithError(ctx, api.ErrInvalidRequest.WithError(err))
		return
	}

	openFile, err := file.Open()
	if err != nil {
		api.ResponseWithError(ctx, api.ErrInvalidRequest.WithError(err))
		return
	}
	defer func() {
		_ = openFile.Close()
	}()

	data, err := io.ReadAll(openFile)
	if err != nil {
		api.ResponseWithError(ctx, api.ErrInvalidRequest.WithError(err))
		return
	}

	s3ObjectID := fmt.Sprintf("%s/source.zip", toolInstance.ID.Hex())
	if err = ctrl.s3.PutObject(ctx, s3ObjectID, ctrl.s3Bucket, data); err != nil {
		log.Warn(ctx).Err(err).Msg("Failed to upload file to S3")
		api.ResponseWithError(ctx, api.ErrInternal.WithMessage("Failed to upload file to S3"))
		return
	}
	toolInstance.S3URI = fmt.Sprintf("s3://%s/%s", ctrl.s3Bucket, s3ObjectID)

	if _, err = ctrl.toolColl.InsertOne(ctx, tool); err != nil {
		log.Warn(ctx).Err(err).Msg("Failed to save Tool to database")
		api.ResponseWithError(ctx, db.ConvertError(err))
		return
	}

	if _, err = ctrl.toolInstancesColl.InsertOne(ctx, toolInstance); err != nil {
		log.Warn(ctx).Err(err).Msg("Failed to save ToolInstance to database")
		api.ResponseWithError(ctx, db.ConvertError(err))
		return
	}
	api.ResponseWithSuccess(ctx, tool)
}

func (ctrl *ToolController) PublishTool(ctx *gin.Context) {
	tool, err := ctrl.getToolByID(ctx)
	if err != nil {
		api.ResponseWithError(ctx, err)
		return
	}
	instance, err := ctrl.getToolInstanceByID(ctx, tool.HeadVersionID)
	if err != nil {
		log.Warn(ctx).Err(err).Msg("Failed to get tool instance")
		api.ResponseWithError(ctx, err)
		return
	}
	if instance.CurrentState != model.ResourceStatusBuilt {
		api.ResponseWithError(ctx, api.ErrInvalidRequest.WithMessage("invalid state, tool state of [ Built ] is required"))
		return
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
		api.ResponseWithError(ctx, db.ConvertError(err))
		return
	}
	api.ResponseWithSuccess(ctx, nil)
}

func (ctrl *ToolController) GetToolSummary(ctx *gin.Context) {

}

func (ctrl *ToolController) GetToolFunction(ctx *gin.Context) {

}

func (ctrl *ToolController) DeleteTool(ctx *gin.Context) {

}

func (ctrl *ToolController) CreateToolVersion(ctx *gin.Context) {

}

func (ctrl *ToolController) GetToolOpenAISchema(ctx *gin.Context) {
	tool, err := ctrl.getToolByID(ctx)
	if err != nil {
		api.ResponseWithError(ctx, err)
		return
	}
	instance, err := ctrl.getToolInstanceByID(ctx, tool.HeadVersionID)
	if err != nil {
		api.ResponseWithError(ctx, err)
		return
	}
	data := instance.OpenAISchema()
	rd := render.Reader{
		Reader:        bytes.NewBuffer(data),
		ContentLength: int64(len(data)),
		ContentType:   "application/json; charset=utf-8",
	}
	ctx.Render(http.StatusOK, rd)
}

// GetToolOpenAPISchema https://api.npi.ai/schemas/{tool_id}
func (ctrl *ToolController) GetToolOpenAPISchema(ctx *gin.Context) {
	tool, err := ctrl.getToolByID(ctx)
	if err != nil {
		api.ResponseWithError(ctx, err)
		return
	}
	instance, err := ctrl.getToolInstanceByID(ctx, tool.HeadVersionID)
	if err != nil {
		api.ResponseWithError(ctx, err)
		return
	}

	data := instance.OpenAPISchema()
	rd := render.Reader{
		Reader:        bytes.NewBuffer(data),
		ContentLength: int64(len(data)),
		ContentType:   "application/yaml; charset=utf-8",
	}
	ctx.Render(http.StatusOK, rd)
}

func (ctrl *ToolController) getToolByID(ctx *gin.Context) (*model.Tool, error) {
	toolID := ctx.Param("tool_id")

	tID, err := primitive.ObjectIDFromHex(toolID)
	if err != nil {
		return nil, api.ErrObjectID
	}

	result := ctrl.toolColl.FindOne(ctx, bson.M{"_id": tID})
	if result.Err() != nil {
		return nil, db.ConvertError(result.Err())
	}
	tool := &model.Tool{}
	_ = result.Decode(&tool)
	return tool, nil
}

func (ctrl *ToolController) getToolInstanceByID(ctx *gin.Context, id primitive.ObjectID) (*model.ToolInstance, error) {
	result := ctrl.toolInstancesColl.FindOne(ctx, bson.M{"_id": id})
	if result.Err() != nil {
		return nil, db.ConvertError(result.Err())
	}
	tool := &model.ToolInstance{}
	_ = result.Decode(&tool)
	return tool, nil
}
