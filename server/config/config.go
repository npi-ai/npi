package config

import (
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/reconcile"
)

type ServerConfig struct {
	Port    int                            `yaml:"port"`
	MongoDB db.MongoConfig                 `yaml:"mongodb"`
	S3      db.S3Config                    `yaml:"s3"`
	Tools   reconcile.ToolReconcilerConfig `yaml:"tools"`
}
