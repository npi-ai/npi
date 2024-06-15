package model

type ResourceStatus string

const (
	ResourceStatusDraft      = ResourceStatus("draft")
	ResourceStatusQueued     = ResourceStatus("queued")
	ResourceStatusUpdated    = ResourceStatus("updated")
	ResourceStatusProcessing = ResourceStatus("processing")
	ResourceStatusRetry      = ResourceStatus("retry")
	ResourceStatusSuccess    = ResourceStatus("success")
	ResourceStatusToBeDelete = ResourceStatus("to_be_deleted")
	ResourceStatusDeleting   = ResourceStatus("deleting")
	ResourceStatusDeleted    = ResourceStatus("deleted")
	ResourceStatusError      = ResourceStatus("error")
	ResourceStatusBuilt      = ResourceStatus("built")
	ResourcePublishing       = ResourceStatus("publishing")
)
