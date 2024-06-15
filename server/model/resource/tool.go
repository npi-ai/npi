package resource

import "github.com/npi-ai/npi/server/model"

type ToolResource struct {
	model.BaseResource `json:",inline" bson:",inline"`
}
