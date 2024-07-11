package utils

import (
	"context"
)

const (
	keyUserID = "user_id"
)

func GetUserID(ctx context.Context) string {
	return getValue(ctx, keyUserID)
}

func getValue(ctx context.Context, key string) string {
	id, ok := ctx.Value(key).(string)
	if !ok {
		return ""
	}
	return id
}
