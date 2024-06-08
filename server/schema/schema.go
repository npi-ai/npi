package schema

import (
	"encoding/json"
	"fmt"
	server "github.com/npi-ai/npi/proto/go/api"
	"strings"
	"time"

	"github.com/pb33f/libopenapi/datamodel/high/base"
	"github.com/pb33f/libopenapi/datamodel/high/v3"
	"github.com/pb33f/libopenapi/orderedmap"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

type ToolExtended struct {
	ID        primitive.ObjectID `json:"id" bson:"_id"`
	ToolID    primitive.ObjectID `json:"tool_id" bson:"tool_id"`
	ToolSpec  server.ToolSpec    `json:"tool_spec" bson:"tool_spec"`
	Hostname  string             `json:"hostname" bson:"hostname"`
	IP        string             `json:"ip" bson:"ip"`
	Port      int                `json:"port" bson:"port"`
	CreatedAt time.Time          `json:"created_at" bson:"created_at"`
	UpdatedAt time.Time          `json:"update_at" bson:"update_at"`
}

func (t *ToolExtended) OpenAISchema() []byte {
	var tools []interface{}
	for _, fc := range t.ToolSpec.FunctionSpec.Functions {
		tools = append(tools, fc.Schema())
	}
	data, _ := json.Marshal(tools)
	return data
}

func (t *ToolExtended) OpenAPISchema() []byte {
	var v3Model = v3.Document{
		Version: "3.1.0",
		Info: &base.Info{
			Title:          t.ToolSpec.Metadata.Name,
			Description:    t.ToolSpec.Metadata.Description,
			TermsOfService: "https://www.npi.ai/terms",
			Contact: &base.Contact{
				Name:  "Support",
				URL:   "https://www.npi.ai/contact",
				Email: "w@npi.ai",
			},
			License: &base.License{
				Name:       "BSL v1.1",
				URL:        "https://github.com/npi-ai/npi/blob/main/LICENSE",
				Identifier: "BUSL-1.1",
			},
			Version: t.ToolSpec.Metadata.Version,
		},
		Servers: []*v3.Server{
			{
				URL: fmt.Sprintf("https://%s.tools.npi.ai", t.ToolSpec.Metadata.Id),
			},
		},
		Paths: &v3.Paths{
			PathItems: orderedmap.New[string, *v3.PathItem](),
		},
	}

	for _, f := range t.ToolSpec.FunctionSpec.Functions {
		v3Model.Paths.PathItems.Set(
			fmt.Sprintf("/%s/%s", t.ToolSpec.Metadata.Name, changeSnakeToCamel(f.Name)),
			f.OpenAPISchema())
	}

	return v3Model.RenderWithIndention(2)
}

func (t *ToolExtended) GetFunctionByName(s string) *server.Function {
	for _, f := range t.ToolSpec.FunctionSpec.Functions {
		if fmt.Sprintf("%s/%s", t.ToolSpec.Metadata.Name, changeSnakeToCamel(f.Name)) == s {
			return f
		}
	}
	return nil
}

func changeSnakeToCamel(str string) string {
	words := strings.FieldsFunc(str, func(r rune) bool { return r == '_' })
	for i := 1; i < len(words); i++ {
		words[i] = strings.Title(words[i])
	}
	return strings.Join(words, "")
}

//type FunctionInstance struct {
//	ToolID     primitive.ObjectID `json:"tool_id" bson:"tool_id"`
//	FunctionID string             `json:"id" bson:"id"`
//	Function   Function           `json:"-" bson:"function"`
//	CreatedAt  int64              `json:"created_at" bson:"created_at"`
//	UpdatedAt  int64              `json:"updated_at" bson:"updated_at"`
//}
