package config

import "github.com/npi-ai/npi/server/db"

type ServerConfig struct {
	Port    int            `yaml:"port"`
	MongoDB db.MongoConfig `yaml:"mongodb"`
	S3      db.S3Config    `yaml:"s3"`
	Storage StorageConfig  `yaml:"storage"`
}

type StorageConfig struct {
	ToolBucket string `yaml:"tool_bucket"`
}
