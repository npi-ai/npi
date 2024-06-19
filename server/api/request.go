package api

type ToolFrom string

const (
	ToolFromGitHub = ToolFrom("github")
	ToolFromZip    = ToolFrom("zip")
)

type ToolRequest struct {
	Name         string   `json:"name"`
	From         ToolFrom `json:"from"`
	GitHubOrg    string   `json:"github_org"`
	GitHubRepo   string   `json:"github_repo"`
	GitHubBranch string   `json:"github_branch"`
	RepoDir      string   `json:"repo_dir"`
}

type UpdateUserProfile struct {
	Nickname string `json:"nickname,omitempty"`
	Picture  string `json:"picture,omitempty"`
}

type UpdateOrgProfile struct {
	Name    string `json:"name,omitempty"`
	Picture string `json:"picture,omitempty"`
}

type MoveAfterForm struct {
	AfterPageID  string `json:"after_page_id" binding:"required"`
	ParentPageID string `json:"parent_page_id" binding:"required"`
}

type InviteNewMemberForm struct {
	Email string `json:"email" binding:"required,email"`
	Role  string `json:"role" binding:"required,oneof=owner admin writer reader"`
}

type UpdateMembershipForm struct {
	Role string `json:"role" binding:"required"`
}

type DeleteMembersForm struct {
	UserIDs []string `json:"user_ids" binding:"required"`
}
