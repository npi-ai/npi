package api

import (
	"errors"
	"github.com/gin-gonic/gin"
	"github.com/npi-ai/npi/server/model"
	"net/http"
)

func ResponseWithSuccess(ctx *gin.Context, data any) {
	if data == nil || &data == nil {
		data = gin.H{}
	}
	ctx.JSONP(http.StatusOK, data)
}

func ResponseWithError(ctx *gin.Context, err error) {
	var em errorMessage
	ok := errors.As(err, &em)
	if ok {
		ctx.JSONP(em.HTTPCode, em)
	} else {
		_ = errors.As(ErrUnknown, &em)
		ctx.JSONP(em.HTTPCode, em.WithError(err))
	}
	ctx.Abort()
}

type ToolSummary struct {
	ID                 string             `json:"id"`
	Name               string             `json:"name"`
	Status             string             `json:"status"`
	Description        string             `json:"description"`
	Runtime            model.Runtime      `json:"runtime"`
	Dependencies       []model.Dependency `json:"dependencies"`
	Authentication     Authentication     `json:"authentication"`
	Endpoint           string             `json:"endpoint"`
	RequiredPermission []string           `json:"-"`
}

type Authentication struct {
	ClientID    string         `json:"client_id"`
	Type        model.AuthType `json:"type"`
	APIKeyLast4 string         `json:"api_key_last4"`
}

type ToolStatus struct {
	Authorized          bool               `json:"authorized"`
	Deployed            bool               `json:"deployed"`
	ClientID            string             `json:"client_id"`
	RequiredPermissions []model.Permission `json:"required_permissions"`
}

type Tool struct {
	model.Tool  `json:",inline"`
	Description string `json:"description"`
	Status      string `json:"status"`
	Functions   int    `json:"functions"`
}
