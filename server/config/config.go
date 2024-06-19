package config

import (
	"github.com/npi-ai/npi/server/reconcile"
)

type ServerConfig struct {
	Tools reconcile.ToolReconcilerConfig `yaml:"tools"`
}
