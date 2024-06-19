package utils

import (
	"context"
)

const (
	keyUserID = "user_id"
	keyOrgID  = "org_id"
)

// GetUserID TODO primitive.ObjectID ?
func GetUserID(ctx context.Context) string {
	return getValue(ctx, keyUserID)
}

func GetOrgID(ctx context.Context) string {
	return getValue(ctx, keyOrgID)
}

func getValue(ctx context.Context, key string) string {
	id, ok := ctx.Value(key).(string)
	if !ok {
		return ""
	}
	return id
}
