package server

import (
	"fmt"
	"github.com/pb33f/libopenapi/datamodel/high/base"
	"github.com/pb33f/libopenapi/datamodel/high/v3"
	"github.com/pb33f/libopenapi/orderedmap"
	"strings"
)

func (f *Function) Arguments(lan Language) string {
	switch lan {
	case Language_PYTHON:
		args := ""
		for _, para := range f.Parameters {
			args += fmt.Sprintf("%s=event['%s'], ", para.Name, para.Name)
		}
		return strings.TrimRight(args, ", ")
	}
	return "unsupported"
}

func (f *Function) Schema() map[string]interface{} {
	properties := map[string]interface{}{}
	var required []string
	for _, para := range f.Parameters {
		properties[para.Name] = map[string]string{
			"type":        para.Type,
			"description": para.Description,
		}
		if para.Required {
			required = append(required, para.Name)
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
				"required":   required,
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
	for _, para := range f.Parameters {
		properties.Set(para.Name, base.CreateSchemaProxy(&base.Schema{
			Type:        []string{para.Type},
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

func changeSnakeToCamel(str string) string {
	words := strings.FieldsFunc(str, func(r rune) bool { return r == '_' })
	for i := 1; i < len(words); i++ {
		words[i] = strings.Title(words[i])
	}
	return strings.Join(words, "")
}
