package service

import (
	"context"
	"testing"

	"github.com/npi-ai/npi/server/db"
)

func Test_Build(t *testing.T) {
	bs := &BuilderService{
		dockerRegistry: "992297059634.dkr.ecr.us-west-2.amazonaws.com",
		s3Bucket:       "npiai-tools-build-test",
		s3Service:      db.NewS3(db.S3Config{}),
		rootDir:        "/Users/wenfeng/tmp/build",
		validateScript: "/Users/wenfeng/workspace/npi-ai/npi/server/scripts/tool_validator.py",
	}

	err := bs.build(context.Background(), ToolMetadata{
		ID:          "github",
		Name:        "github123",
		Version:     "0.1.0",
		Description: "123",
		Authors:     []string{"wenfeng"},
	})
	println(err)
}
