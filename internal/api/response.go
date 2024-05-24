package api

import (
	"errors"
	"github.com/gin-gonic/gin"
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
