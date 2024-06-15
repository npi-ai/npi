package model

import (
	"context"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"time"
)

func NewBaseResource(ctx context.Context) BaseResource {
	return BaseResource{
		ID:        primitive.NewObjectID(),
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

type BaseResource struct {
	ID           primitive.ObjectID `json:"id" bson:"_id"`
	CreatedAt    time.Time          `json:"created_at" bson:"created_at"`
	UpdatedAt    time.Time          `json:"updated_at" bson:"updated_at"`
	Times        int                `json:"-" bson:"retry_times"`
	ScheduledAt  time.Time          `json:"-" bson:"scheduled_at"`
	Err          string             `json:"-" bson:"error,omitempty"`
	SourceState  ResourceStatus     `json:"-" bson:"source_state"`
	TargetState  ResourceStatus     `json:"-" bson:"target_state"`
	CurrentState ResourceStatus     `json:"-" bson:"current_state"`
	StateHistory []ResourceStatus   `json:"-" bson:"state_history"`
	InProgress   bool               `json:"-" bson:"in_progress"`
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
