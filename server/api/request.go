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
