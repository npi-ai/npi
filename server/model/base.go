package model

import (
	"context"
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

func NewBase(ctx context.Context) Base {
	return Base{
		ID:        primitive.NewObjectID(),
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

type Base struct {
	ID        primitive.ObjectID `json:"id" bson:"_id"`
	CreatedAt time.Time          `json:"created_at" bson:"created_at"`
	UpdatedAt time.Time          `json:"updated_at" bson:"updated_at"`
	CreatedBy string             `json:"created_by" bson:"created_by"`
	UpdatedBy string             `json:"updated_by" bson:"updated_by"`
}

func (b Base) ObjectID() primitive.ObjectID {
	return b.ID
}

func NewBaseResource(ctx context.Context) BaseResource {
	b := Base{
		ID:        primitive.NewObjectID(),
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	return BaseResource{
		Base:    b,
		RetryAt: b.CreatedAt,
	}
}

type BaseResource struct {
	Base         `json:",inline" bson:",inline"`
	Times        int              `json:"-" bson:"retry_times"`
	RetryAt      time.Time        `json:"-" bson:"retry_at"`
	Err          string           `json:"-" bson:"error,omitempty"`
	SourceState  ResourceStatus   `json:"-" bson:"source_state"`
	TargetState  ResourceStatus   `json:"-" bson:"target_state"`
	CurrentState ResourceStatus   `json:"-" bson:"current_state"`
	StateHistory []ResourceStatus `json:"-" bson:"state_history"`
	InProgress   bool             `json:"-" bson:"in_progress"`
}

func (b BaseResource) RetryTimes() int {
	return b.Times
}
