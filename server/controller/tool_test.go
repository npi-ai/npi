package controller

import (
	"context"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/npi-ai/npi/server/config"
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/reconcile"
	"gopkg.in/yaml.v3"
	"os"
	"testing"
)

func TestToolController(t *testing.T) {
	data, _ := os.ReadFile("/Users/wenfeng/workspace/npi-ai/npi/credentials/server.yml")
	cfg := config.ServerConfig{}
	_ = yaml.Unmarshal(data, &cfg)
	ctx := context.Background()
	db.InitMongoDB(ctx, cfg.MongoDB)
	db.InitS3(cfg.S3)

	toolReconciler := reconcile.NewToolReconciler()
	_ = toolReconciler.Start(ctx)
	ctrl := NewTool(cfg.Storage.ToolBucket)
	if ctrl == nil {
		panic("NewTool should not return nil")
	}
	engine := gin.New()
	rootGroup := engine.Group("")
	if err := ctrl.RegisterRoute(rootGroup); err != nil {
		t.Error("RegisterRoute should not return error")
	}
	if err := engine.Run(fmt.Sprintf("0.0.0.0:%d", cfg.Port)); err != nil {
		panic(fmt.Sprintf("failed to start HTTP server: %s", err))
	}
}
