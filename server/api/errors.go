package api

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
)

var (
	ErrParseBody      = newErrorMessage(http.StatusBadRequest, 40001, "invalid request body")
	ErrInvalidRequest = newErrorMessage(http.StatusBadRequest, 40002, "invalid request parameters")
	ErrObjectID       = newErrorMessage(http.StatusBadRequest, 40003, "invalid object id")
	ErrFailedExchange = newErrorMessage(http.StatusBadRequest, 40004, "failed to exchange an authorization code for a token")

	ErrUnauthorized = newErrorMessage(http.StatusUnauthorized, 40101, "unauthorized")

	ErrNoCardFound      = newErrorMessage(http.StatusPaymentRequired, 40201, "No card found, please add a card")
	ErrNoSeatsAvailable = newErrorMessage(http.StatusPaymentRequired, 40202, "No seats available, please upgrade your plan or buy seats")

	ErrNoPermission = newErrorMessage(http.StatusForbidden, 40301, "no permission")

	ErrFunctionNotFound = newErrorMessage(http.StatusNotFound, 40401, "function not found")
	ErrResourceNotFound = newErrorMessage(http.StatusNotFound, 40402, "resource not found")
	DocumentNotFound    = newErrorMessage(http.StatusNotFound, 40403, "data not found in database")

	ErrNotAllowed = newErrorMessage(http.StatusMethodNotAllowed, 40501, "method not allowed")

	ErrCannotLeave         = newErrorMessage(http.StatusConflict, 40901, "cannot leave the org")
	ErrUserAlreadyIsMember = newErrorMessage(http.StatusConflict, 40902, "user already is a membership")
	ErrOperationImpossible = newErrorMessage(http.StatusConflict, 40903, "impossible operation")

	ErrInternal      = newErrorMessage(http.StatusInternalServerError, 50001, "internal error")
	ErrUnknown       = newErrorMessage(http.StatusInternalServerError, 50002, "unknown error")
	ErrResourceRetry = newErrorMessage(http.StatusInternalServerError, 50003, "resource retry")
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
	return e1.ErrCode == e2.ErrCode
}

type ErrorMessage interface {
	error
	WithMessage(msg string) ErrorMessage
	WithError(err error) ErrorMessage
	IsSame(err error) bool
	Msg() string
}

type errorMessage struct {
	Err      string `json:"error,omitempty"`
	Message  string `json:"message,omitempty"`
	HTTPCode int    `json:"http_code"`
	ErrCode  int    `json:"error_code"`
}

func newErrorMessage(httpCode, appCode int, defaultMsg string) ErrorMessage {
	return errorMessage{
		HTTPCode: httpCode,
		ErrCode:  appCode,
		Message:  defaultMsg,
	}
}
func (em errorMessage) WithError(err error) ErrorMessage {
	if err == nil {
		return em
	}
	underlayErr := &errorMessage{}
	if errors.As(err, underlayErr) {
		return em.WithMessage(fmt.Sprintf("%s, %s\n", underlayErr.Err, underlayErr.Message))
	}
	return em.WithMessage(err.Error())
}

func (em errorMessage) WithMessage(msg string) ErrorMessage {
	if msg == "" {
		return em
	}
	m := errorMessage{
		HTTPCode: em.HTTPCode,
		ErrCode:  em.ErrCode,
		Err:      em.Err,
		Message:  msg,
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
	return em.ErrCode == m.ErrCode
}

func (em errorMessage) Msg() string {
	return em.Message
}
