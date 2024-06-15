package model

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
