package utils

import (
	"math/rand"
	"strings"
	"time"
)

var (
	rd = rand.New(rand.NewSource(time.Now().UnixNano()))
)

func GenerateRandomString(length int, includeNumber bool, includeSpecial bool) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
	var password []byte
	var builder strings.Builder

	if includeNumber {
		builder.WriteString("0123456789")
	}
	if includeSpecial {
		builder.WriteString("!@#$%^&*()_+=-")
	}
	builder.WriteString(charset)
	charSource := builder.String()

	for i := 0; i < length; i++ {
		randNum := rd.Intn(len(charSource))
		password = append(password, charSource[randNum])
	}
	return string(password)
}
