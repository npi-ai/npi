package utils

import (
	"math/rand"
	"strings"
	"time"
)

var (
	rd = rand.New(rand.NewSource(time.Now().UnixNano()))
)

const lowercase = "abcdefghijklmnopqrstuvwxyz"
const uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

func GenerateRandomString(length int, includeUppercase, includeNumber, includeSpecial bool) string {
	var password []byte
	var builder strings.Builder
	builder.WriteString(lowercase)
	if includeUppercase {
		builder.WriteString(uppercase)
	}
	if includeNumber {
		builder.WriteString("0123456789")
	}
	if includeSpecial {
		builder.WriteString("!@#$%^&*()_+=-")
	}
	charSource := builder.String()

	rd := rand.New(rand.NewSource(time.Now().UnixNano()))
	for i := 0; i < length; i++ {
		randNum := rd.Intn(len(charSource))
		password = append(password, charSource[randNum])
	}
	return string(password)
}
