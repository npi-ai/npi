from pydantic import Field
from textwrap import dedent
from npi.types import Parameters
from typing import Optional, List, Literal


class SearchParameters(Parameters):
    query: str = Field(
        description=dedent(
            """
            Search query to search for GitHub issues and pull requests. Below are some query examples:
            
            1. Search for all issues containing "performance" in the repository npi/npi: `is:issue repo:npi/npi performance`
            2. Search for open pull requests in repository npi/npi: `is:pr is:open repo:npi/npi`
            """
        )
    )


class GetIssueParameters(Parameters):
    repository: str = Field(description="GitHub repository in the format {owner}/{repo}. Ask the user if not provided.")
    number: int = Field(description="Issue's number. Ask the user if not provided.")


class GetPullRequestParameters(Parameters):
    repository: str = Field(description="GitHub repository in the format {owner}/{repo}. Ask the user if not provided.")
    number: int = Field(description="Pull Request's number. Ask the user if not provided.")


class CreateIssueParameters(Parameters):
    repository: str = Field(description="GitHub repository in the format {owner}/{repo}. Ask the user if not provided.")
    title: str = Field(description="Issue's title")
    body: str = Field(description="Issue's body in markdown format")
    labels: Optional[List[str]] = Field(default=None, description="List of labels to add to the issue")
    assignees: Optional[List[str]] = Field(default=None, description="List of users to assign to the issue")


class CreatePullRequestParameters(Parameters):
    repository: str = Field(description="GitHub repository in the format {owner}/{repo}. Ask the user if not provided.")
    title: str = Field(description="Pull Request's title")
    body: str = Field(description="Pull Request's body in markdown format")
    base: str = Field(description="Base branch of the pull request, i.e., the branch to merge the pull request into")
    head: str = Field(description="Head branch of the pull request, i.e., the branch with your changes")
    is_draft: Optional[bool] = Field(default=False, description="Whether this pull request is a draft or not")
    labels: Optional[List[str]] = Field(default=None, description="List of labels to add to the pull request")
    assignees: Optional[List[str]] = Field(default=None, description="List of users to assign to the pull request")


class AddIssueCommentParameters(GetIssueParameters):
    body: str = Field(description="Comment's body in markdown format")


class AddPullRequestCommentParameters(GetPullRequestParameters):
    body: str = Field(description="Comment's body in markdown format")


class EditIssueParameters(GetIssueParameters):
    title: Optional[str] = Field(default=None, description="Issue's title")
    body: Optional[str] = Field(default=None, description="Issue's body in markdown format")
    labels: Optional[List[str]] = Field(default=None, description="List of labels to add to the issue")
    assignees: Optional[List[str]] = Field(default=None, description="List of users to assign to the issue")
    state: Optional[Literal['open', 'closed']] = Field(
        default=None, description="Issue state, either 'open' or 'closed'"
    )


class EditPullRequestParameters(GetPullRequestParameters):
    title: Optional[str] = Field(default=None, description="Pull Request's title")
    body: Optional[str] = Field(default=None, description="Pull Request's body in markdown format")
    base: Optional[str] = Field(
        default=None, description="Base branch of the pull request, i.e., the branch to merge the pull request into"
    )
    labels: Optional[List[str]] = Field(default=None, description="List of labels to add to the pull request")
    assignees: Optional[List[str]] = Field(default=None, description="List of users to assign to the pull request")
    state: Optional[Literal['open', 'closed']] = Field(
        default=None, description="Pull Request state, either 'open' or 'closed'"
    )
