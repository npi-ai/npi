package log

import (
	"context"
	"github.com/gin-contrib/requestid"
	"github.com/gin-gonic/gin"
	"github.com/rs/zerolog"
	"os"
)

var lg zerolog.Logger

const (
	requestId = "request_id"
)

func init() {
	lg = zerolog.New(os.Stdout).Output(zerolog.NewConsoleWriter()).With().Caller().Timestamp().Logger()
}

func SetLoggerLevel(level zerolog.Level) {
	lg = lg.Level(level)
}

func Debug(ctx ...context.Context) *zerolog.Event {
	e := lg.Debug()

	if len(ctx) > 0 {
		gCtx, ok := ctx[0].(*gin.Context)
		if ok {
			e.Str(requestId, requestid.Get(gCtx))
		}
	}
	return e
}

func Info(ctx ...context.Context) *zerolog.Event {
	e := lg.Info()

	if len(ctx) > 0 {
		gCtx, ok := ctx[0].(*gin.Context)
		if ok {
			e.Str(requestId, requestid.Get(gCtx))
		}
	}
	return e
}

func Warn(ctx ...context.Context) *zerolog.Event {
	e := lg.Warn()
	if len(ctx) > 0 {
		gCtx, ok := ctx[0].(*gin.Context)
		if ok {
			e.Str(requestId, requestid.Get(gCtx))
		}
	}
	return e
}

func Error(ctx ...context.Context) *zerolog.Event {
	e := lg.Error()
	if len(ctx) > 0 {
		gCtx, ok := ctx[0].(*gin.Context)
		if ok {
			e.Str(requestId, requestid.Get(gCtx))
		}
	}
	return e
}
