package utils

import (
	"context"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

func GetUserID(ctx context.Context) string {
	return "system"
}

func GetOrgID(ctx context.Context) primitive.ObjectID {
	return primitive.NilObjectID
}
