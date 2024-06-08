package controller

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/render"
	"github.com/npi-ai/npi/internal/api"
	"github.com/npi-ai/npi/internal/db"
	"github.com/npi-ai/npi/internal/log"
	"github.com/npi-ai/npi/internal/schema"
	"go.mongodb.org/mongo-driver/bson"
)

func (ctrl *Controller) startRouter(ctx context.Context, port int) {
	r := gin.Default()
	{
		r.GET("/:tool_id", ctrl.LookupTool)
		r.GET("/:tool_id/openai-schema", ctrl.GetToolOpenAISchema)
		r.GET("/:tool_id/openapi-schema", ctrl.GetToolOpenAPISchema)
	}

	log.Info().Int("port", port).Msg("starting router")
	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", port),
		Handler: r,
	}
	go func() {
		<-ctx.Done()
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := server.Shutdown(ctx); err != nil {
			log.Error().Err(err).Msg("failed to shutdown router")
		} else {
			log.Info().Msg("router exited")
		}
	}()

	err := server.ListenAndServe()
	if !errors.Is(err, http.ErrServerClosed) {
		panic(fmt.Sprintf("failed to start router: %v", err))
	}
}

func (ctrl *Controller) LookupTool(ctx *gin.Context) {

}

func (ctrl *Controller) GetToolOpenAISchema(ctx *gin.Context) {
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
func (ctrl *Controller) GetToolOpenAPISchema(ctx *gin.Context) {
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

func (ctrl *Controller) getToolByID(ctx *gin.Context) (*schema.ToolExtended, error) {
	toolID := ctx.Param("tool_id")
	if tool, ok := toolCache.Load(toolID); ok {
		return tool.(*schema.ToolExtended), nil
	}

	result := ctrl.toolSpecColl.FindOne(ctx, bson.M{"metadata.id": toolID})
	if result.Err() != nil {
		return nil, db.ConvertError(result.Err())
	}
	tool := &schema.ToolExtended{}
	_ = result.Decode(&tool)
	toolCache.Store(toolID, tool)
	return tool, nil
}
