package service

import (
	"context"
	"testing"

	"github.com/npi-ai/npi/server/model"
)

func Test_Build(t *testing.T) {
	bs := NewBuilderService(
		"992297059634.dkr.ecr.us-west-2.amazonaws.com",
		"npiai-tools-build-test",
		"/Users/wenfeng/tmp/build",
		"/Users/wenfeng/workspace/npi-ai/npi/server/scripts/tool_validator.py",
	)

	err := bs.Build(context.Background(), model.ToolMetadata{
		ID:          "github",
		Name:        "github123",
		Description: "123",
		Authors:     []string{"wenfeng"},
	})
	println(err)
}
