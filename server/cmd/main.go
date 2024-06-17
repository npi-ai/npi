package main

import (
	"context"
	"fmt"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/npi-ai/npi/server/config"
	"github.com/npi-ai/npi/server/controller"
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/reconcile"
	"gopkg.in/yaml.v3"
)

func main() {
	data, err := os.ReadFile(os.Getenv("SERVER_CONFIG"))
	if err != nil {
		panic(fmt.Sprintf("failed to read config file: %s", err))
	}
	cfg := config.ServerConfig{}
	if err = yaml.Unmarshal(data, &cfg); err != nil {
		panic(fmt.Sprintf("failed to unmarshal config file: %s", err))
	}
	ctx := context.Background()
	db.InitMongoDB(ctx, cfg.MongoDB)
	db.InitS3(cfg.S3)

	toolReconciler := reconcile.NewToolReconciler(cfg.Tools)
	_ = toolReconciler.Start(ctx)
	ctrl := controller.NewTool(cfg.Tools.S3Bucket)
	if ctrl == nil {
		panic("NewTool should not return nil")
	}
	engine := gin.New()
	rootGroup := engine.Group("")
	if err := ctrl.RegisterRoute(rootGroup); err != nil {
		panic("RegisterRoute should not return error")
	}
	if err := engine.Run(fmt.Sprintf("0.0.0.0:%d", cfg.Port)); err != nil {
		panic(fmt.Sprintf("failed to start HTTP server: %s", err))
	}
}
