package api

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
)

var (
	ErrParseBody      = newErrorMessage(http.StatusBadRequest, 40001, "parse body error")
	ErrInvalidRequest = newErrorMessage(http.StatusBadRequest, 40002, "invalid request")
	ErrObjectID       = newErrorMessage(http.StatusBadRequest, 40003, "invalid object id")

	ErrUnauthorized = newErrorMessage(http.StatusUnauthorized, 40101, "unauthorized")

	ErrNoPermission = newErrorMessage(http.StatusForbidden, 40301, "no permission")

	ErrFunctionNotFound = newErrorMessage(http.StatusNotFound, 40401, "function not found")
	ErrResourceNotFound = newErrorMessage(http.StatusNotFound, 40402, "resource not found")
	DocumentNotFound    = newErrorMessage(http.StatusNotFound, 40403, "data not found in database")

	ErrInternal = newErrorMessage(http.StatusInternalServerError, 50001, "internal error")
	ErrUnknown  = newErrorMessage(http.StatusInternalServerError, 50002, "unknown error")
)

func IsErrNotFound(err error) bool {
	var e errorMessage
	ok := errors.As(err, &e)
	if !ok {
		return false
	}
	return e.HTTPCode == http.StatusNotFound
}

func IsError(err1, err2 error) bool {
	var e1 errorMessage
	ok := errors.As(err1, &e1)
	if !ok {
		return false
	}
	var e2 errorMessage
	ok = errors.As(err2, &e2)
	if !ok {
		return false
	}
	return e1.AppCode == e2.AppCode
}

type ErrorMessage interface {
	error
	WithMessage(msg string) ErrorMessage
	WithError(err error) ErrorMessage
	IsSame(err error) bool
	Msg() string
}

type errorMessage struct {
	Err      string `json:"error"`
	Message  string `json:"message,omitempty"`
	HTTPCode int    `json:"http_code"`
	AppCode  int    `json:"app_code"`
}

func newErrorMessage(httpCode, appCode int, errorMsg string) ErrorMessage {
	return errorMessage{
		HTTPCode: httpCode,
		AppCode:  appCode,
		Err:      errorMsg,
	}
}
func (em errorMessage) WithError(err error) ErrorMessage {
	if err == nil {
		return em
	}
	return em.WithMessage(err.Error())
}

func (em errorMessage) WithMessage(msg string) ErrorMessage {
	if msg == "" {
		return em
	}
	m := errorMessage{
		HTTPCode: em.HTTPCode,
		AppCode:  em.AppCode,
		Err:      em.Err,
		Message:  msg,
	}
	if em.Message != "" {
		m.Message = fmt.Sprintf("%s\n%s", msg, em.Message)
	}
	return m
}

func (em errorMessage) Error() string {
	data, _ := json.Marshal(em)
	return string(data)
}

func (em errorMessage) IsSame(err error) bool {
	var m errorMessage
	ok := errors.As(err, &m)
	if !ok {
		return false
	}
	return em.AppCode == m.AppCode
}

func (em errorMessage) Msg() string {
	return em.Message
}
