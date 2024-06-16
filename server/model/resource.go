package model

import (
	"context"
	"github.com/npi-ai/npi/server/utils"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"time"
)

type Base struct {
	ID        primitive.ObjectID `json:"id" bson:"_id"`
	CreatedAt time.Time          `json:"created_at" bson:"created_at"`
	UpdatedAt time.Time          `json:"updated_at" bson:"updated_at"`
	CreatedBy string             `json:"created_by" bson:"created_by"`
	UpdatedBy string             `json:"updated_by" bson:"updated_by"`
}

func NewBase(ctx context.Context) Base {
	return Base{
		ID:        primitive.NewObjectID(),
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		CreatedBy: utils.GetUserID(ctx),
		UpdatedBy: utils.GetUserID(ctx),
	}
}

func NewBaseResource(ctx context.Context) BaseResource {
	return BaseResource{
		Base: NewBase(ctx),
	}
}

type BaseResource struct {
	Base         `json:",inline" bson:",inline"`
	Times        int              `json:"-" bson:"retry_times"`
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

func (b BaseResource) ObjectID() primitive.ObjectID {
	return b.ID
}

type ResourceStatus string

const (
	ResourceStatusDraft        = ResourceStatus("draft")
	ResourceStatusQueued       = ResourceStatus("queued")
	ResourceStatusDeploying    = ResourceStatus("deploying")
	ResourceStatusRunning      = ResourceStatus("running")
	ResourceStatusDeleteMarked = ResourceStatus("delete_marked")
	ResourceStatusDeleting     = ResourceStatus("deleting")
	ResourceStatusDeleted      = ResourceStatus("deleted")
	ResourceStatusPauseMarked  = ResourceStatus("pause_marked")
	ResourceStatusPausing      = ResourceStatus("pausing")
	ResourceStatusPaused       = ResourceStatus("paused")
	ResourceStatusError        = ResourceStatus("error")
)
