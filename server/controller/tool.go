package controller

import (
	"bytes"
	"net/http"
	"sync"

	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/render"
	"github.com/npi-ai/npi/server/api"
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/model"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
)

type IController interface {
	RegisterRoute(parent *gin.RouterGroup) error
}

type ToolController struct {
	tollCollection        *mongo.Collection
	toolVersionCollection *mongo.Collection
}

func NewTool() IController {
	return &ToolController{
		tollCollection:        db.GetCollection(db.CollTools),
		toolVersionCollection: db.GetCollection(db.CollToolVersions),
	}
}

func (ctrl *ToolController) RegisterRoute(parent *gin.RouterGroup) error {
	toolRouter := parent.Group("/tools")
	toolRouter.POST("/", ctrl.CreateTool)
	toolRouter.GET("/:tool_id/summary", ctrl.GetToolSummary)
	toolRouter.GET("/:tool_id/functions", ctrl.GetToolFunction)
	toolRouter.DELETE("/:tool_id", ctrl.DeleteTool)
	toolRouter.POST("/:tool_id/version", ctrl.CreateToolVersion)
	toolRouter.GET("/:tool_id/openai", ctrl.GetToolOpenAISchema)
	toolRouter.GET("/:tool_id/openapi", ctrl.GetToolOpenAPISchema)
	return nil
}

func (ctrl *ToolController) CreateTool(ctx *gin.Context) {

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
	data := tool.OpenAISchema()
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

	data := tool.OpenAPISchema()
	rd := render.Reader{
		Reader:        bytes.NewBuffer(data),
		ContentLength: int64(len(data)),
		ContentType:   "application/yaml; charset=utf-8",
	}
	ctx.Render(http.StatusOK, rd)
}

var (
	toolCache = sync.Map{}
)

func (ctrl *ToolController) getToolByID(ctx *gin.Context) (*model.Tool, error) {
	toolID := ctx.Param("tool_id")
	if tool, ok := toolCache.Load(toolID); ok {
		return tool.(*model.Tool), nil
	}

	result := ctrl.tollCollection.FindOne(ctx, bson.M{"metadata.id": toolID})
	if result.Err() != nil {
		return nil, db.ConvertError(result.Err())
	}
	tool := &model.Tool{}
	_ = result.Decode(&tool)
	toolCache.Store(toolID, tool)
	return tool, nil
}
