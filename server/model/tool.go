package model

import (
	"encoding/json"
	"fmt"
	"github.com/pb33f/libopenapi/datamodel/high/base"
	"github.com/pb33f/libopenapi/datamodel/high/v3"
	"github.com/pb33f/libopenapi/orderedmap"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"strings"
)

type Tool struct {
	Base          `json:",inline" bson:",inline"`
	OrgID         primitive.ObjectID `json:"org_id" bson:"org_id"`
	Name          string             `json:"name" bson:"name"`
	HeadVersionID primitive.ObjectID `json:"head_version_id" bson:"head_version_id"`
	Auth          Authentication     `json:"auth" bson:"auth"`
}

type AuthType string

const (
	AuthNone   = AuthType("none")
	AuthAPIKey = AuthType("api_key")
	AuthOAuth  = AuthType("oauth")
)

type Authentication struct {
	Type   AuthType `json:"type" bson:"type"`
	APIKey string   `json:"api_key" bson:"api_key"`
	OAuth  OAuthApp `json:"oauth" bson:"oauth"`
}

type OAuthApp struct {
	ClientID    string `json:"client_id" bson:"client_id"`
	Secrets     string `json:"secrets" bson:"secrets"`
	RedirectURL string `json:"redirect_url" bson:"redirect_url"`
}

type ToolInstance struct {
	BaseResource `json:",inline" bson:",inline"`
	ToolID       primitive.ObjectID `json:"tool_id" bson:"tool_id"`
	OrgID        primitive.ObjectID `json:"org_id" bson:"org_id"`
	Version      string             `json:"version" bson:"version"`
	Metadata     ToolMetadata       `json:"metadata" bson:"metadata"`
	FunctionSpec ToolFunctionSpec   `json:"spec" bson:"spec"`
	Image        string             `json:"image" bson:"image"`
	S3URI        string             `json:"s3_uri" bson:"s3_uri"`
	Hostname     string             `json:"hostname" bson:"hostname"`
	IP           string             `json:"ip" bson:"ip"`
	Port         int                `json:"port" bson:"port"`
	Endpoint     string             `json:"endpoint" bson:"endpoint"`
}

func (t *ToolInstance) OpenAISchema() []byte {
	var tools []interface{}
	for _, fc := range t.FunctionSpec.Functions {
		tools = append(tools, fc.Schema())
	}
	data, _ := json.Marshal(tools)
	return data
}

func (t *ToolInstance) OpenAPISchema() []byte {
	var v3Model = v3.Document{
		Version: "3.1.0",
		Info: &base.Info{
			Title:          t.Metadata.Name,
			Description:    t.Metadata.Description,
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
		},
		Servers: []*v3.Server{
			{
				URL: fmt.Sprintf("https://%s.tools.npi.ai", t.Metadata.ID),
			},
		},
		Paths: &v3.Paths{
			PathItems: orderedmap.New[string, *v3.PathItem](),
		},
	}

	for _, f := range t.FunctionSpec.Functions {
		v3Model.Paths.PathItems.Set(
			fmt.Sprintf("/%s/%s", t.Metadata.Name, changeSnakeToCamel(f.Name)),
			f.OpenAPISchema())
	}

	return v3Model.RenderWithIndention(2)
}

func (t *ToolInstance) GetFunctionByName(s string) Function {
	for _, f := range t.FunctionSpec.Functions {
		if fmt.Sprintf("%s/%s", t.Metadata.Name, changeSnakeToCamel(f.Name)) == s {
			return f
		}
	}
	return Function{}
}

func changeSnakeToCamel(str string) string {
	words := strings.FieldsFunc(str, func(r rune) bool { return r == '_' })
	for i := 1; i < len(words); i++ {
		words[i] = strings.Title(words[i])
	}
	return strings.Join(words, "")
}

type ToolMetadata struct {
	ID          string   `json:"id" bson:"id"`
	Name        string   `json:"name" bson:"name"`
	Description string   `json:"description" bson:"description"`
	Authors     []string `json:"authors" bson:"authors"`
}

type ToolFunctionSpec struct {
	Runtime      Runtime      `json:"runtime" bson:"runtime"`
	Dependencies []Dependency `json:"dependencies" bson:"dependencies"`
	Functions    []Function   `json:"functions" bson:"functions"`
}

type Language string

const (
	Python = Language("python")
)

type Runtime struct {
	Lang    Language `json:"language" bson:"language"`
	Version string   `json:"version" bson:"version"`
	Image   string   `json:"image" bson:"image"`
}

type Dependency struct {
	Name    string `json:"name" bson:"name"`
	Version string `json:"version" bson:"version"`
}

type Function struct {
	Name        string     `json:"name" bson:"name"`
	Description string     `json:"description" bson:"description"`
	Parameters  Parameters `json:"parameters" bson:"parameters"`
	FewShots    []FewShot  `json:"fewShots" bson:"few_shots"`
}

func (f *Function) Arguments(lan Language) string {
	switch lan {
	case Python:
		args := ""
		for _, para := range f.Parameters.Properties {
			args += fmt.Sprintf("%s=event['%s'], ", para.Name, para.Name)
		}
		return strings.TrimRight(args, ", ")
	}
	return "unsupported"
}

func (f *Function) Schema() map[string]interface{} {
	properties := map[string]interface{}{}
	for _, para := range f.Parameters.Properties {
		properties[para.Name] = map[string]string{
			"type":        para.Type.Name(),
			"description": para.Description,
		}
	}

	schema := map[string]interface{}{
		"type": "function",
		"function": map[string]interface{}{
			"name":        f.Name,
			"description": f.Description,
			"parameters": map[string]interface{}{
				"type":       "object",
				"properties": properties,
				"required":   f.Parameters.Required,
			},
		},
	}
	return schema
}

func (f *Function) OpenAPISchema() *v3.PathItem {
	defaultResponse := &v3.Response{
		Description: "successful operation",
		Content:     orderedmap.New[string, *v3.MediaType](),
	}
	media := &v3.MediaType{
		Examples: orderedmap.New[string, *base.Example](),
	}
	media.Examples.Set("application/json", &base.Example{})
	defaultResponse.Content.Set("application/json", media)
	responses := &v3.Responses{
		Codes: orderedmap.New[string, *v3.Response](),
	}
	responses.Codes.Set("200", defaultResponse)
	responses.Default = defaultResponse

	content := orderedmap.New[string, *v3.MediaType]()
	properties := orderedmap.New[string, *base.SchemaProxy]()
	for _, para := range f.Parameters.Properties {
		properties.Set(para.Name, base.CreateSchemaProxy(&base.Schema{
			Type:        []string{para.Type.Name()},
			Description: para.Description,
		}))
	}
	content.Set("application/json", &v3.MediaType{
		Schema: base.CreateSchemaProxy(&base.Schema{
			Type:       []string{"object"},
			Properties: properties,
		}),
	})
	item := &v3.PathItem{
		Post: &v3.Operation{
			Description: f.Description,
			OperationId: changeSnakeToCamel(f.Name),
			//Parameters:  params,
			Responses: responses,
		},
	}
	if properties.Len() > 0 {
		item.Post.RequestBody = &v3.RequestBody{
			Content: content,
		}
	}

	return item
}

type ParameterType string

func (pt ParameterType) Name() string {
	switch pt {
	case String:
		return "string"
	case Int:
		return "integer"
	case Float:
		return "number"
	case Bool:
		return "boolean"
	case Map:
		return "object"
	case List:
		return "array"
	}
	return "unsupported"
}

const (
	String = ParameterType("string")
	Int    = ParameterType("integer")
	Float  = ParameterType("number")
	Bool   = ParameterType("bool")
	Map    = ParameterType("object")
	List   = ParameterType("array")
)

type Parameters struct {
	Description string              `json:"description" bson:"description"`
	Type        ParameterType       `json:"type" bson:"type"`
	Required    []string            `json:"required" bson:"required"`
	Properties  map[string]Property `json:"properties" bson:"properties"`
}

type Property struct {
	Name        string        `json:"name" bson:"name"`
	Description string        `json:"description" bson:"description"`
	Type        ParameterType `json:"type" bson:"type"`
}

type FewShot struct {
	Instruction string `json:"instruction" bson:"instruction"`
	Calling     string `json:"calling" bson:"calling"`
	Result      string `json:"result" bson:"result"`
}
