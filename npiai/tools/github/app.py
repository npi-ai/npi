import json
import os

from github import Github as PyGithub, Auth
from github.IssueComment import IssueComment
from github.Issue import Issue
from github.PullRequestComment import PullRequestComment
from github.PullRequest import PullRequest
from github.GithubObject import NotSet
from typing import Union, TypeVar, List, Literal

from npiai import FunctionTool, function, utils
from npiai.constant import app
from npiai.context import Context
from npiai.error.auth import UnauthorizedError

__PROMPT__ = """
You are a GitHub Agent helping users to manage their issues and pull requests.

## Example

Task: Get the latest issue from npi-ai/npi
Steps:
- get_issue_pr({ "query": "repo:npi-ai/npi is:issue", "max_results": 1 })

Task: Star and fork npi-ai/npi.
Steps:
- star({ "repo": "npi-ai/npi" })
- fork({ "repo": "npi-ai/npi" })

Task: Leave a comment in issue #42 from npi-ai/npi.
Steps:
- add_issue_comment({ "repo": "npi-ai/npi", id: 42, "body": "{{issue_comment}}" })
"""

_T = TypeVar("_T")


def _default_not_set(value: _T) -> _T | "NotSet":
    return value if value is not None else NotSet


class GitHub(FunctionTool):
    name = "github"
    description = "Manage GitHub issues and pull requests"
    system_prompt = __PROMPT__

    _token: str | None
    _client: PyGithub | None

    def __init__(self, access_token: str = None):
        super().__init__()
        self._token = access_token or os.environ.get("GITHUB_ACCESS_TOKEN", None)

    @classmethod
    def from_context(cls, ctx: Context) -> "GitHub":
        if not utils.is_cloud_env():
            raise RuntimeError(
                "GitHub tool can only be initialized from context in the NPi cloud environment"
            )
        creds = ctx.credentials(app_code=app.GITHUB)
        return GitHub(access_token=creds["access_token"])

    async def start(self):
        if self._token is None:
            raise UnauthorizedError("GitHub credentials are not found")
        self._client = PyGithub(auth=Auth.Token(self._token))
        await super().start()

    @staticmethod
    def _comment_to_json(comment: Union[IssueComment, PullRequestComment]):
        """
        Converts a Comment object to a JSON object
        Args:
            comment: an IssueComment or PullRequestComment object

        Returns:
            a JSON object
        """
        return {
            "id": comment.id,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat(),
            "author": comment.user.login,
            "body": comment.body,
        }

    @staticmethod
    def _issue_pr_to_json(issue_or_pr: Union[Issue, PullRequest]):
        """
        Converts an Issue object to a JSON object
        Args:
            issue_or_pr: an Issue or PullRequest object

        Returns:
            a JSON object
        """
        return {
            "number": issue_or_pr.number,
            "title": issue_or_pr.title,
            "created_at": issue_or_pr.created_at.isoformat(),
            "updated_at": issue_or_pr.updated_at.isoformat(),
            "is_closed": issue_or_pr.closed_at is not None,
            "author": issue_or_pr.user.login,
            "body": issue_or_pr.body,
            "comments_count": issue_or_pr.comments,
            "assignees": [user.login for user in issue_or_pr.assignees],
            "labels": [label.name for label in issue_or_pr.labels],
        }

    def _get_issue(self, repo_name: str, number: int) -> Issue:
        """
        Get an issue from the given repository

        Args:
            repo_name: name of the repository in format {owner}/{repo}
            number: issue number

        Returns:
            an Issue object
        """
        repo = self._client.get_repo(repo_name)
        return repo.get_issue(int(number))

    def _get_pull_request(self, repo_name: str, number: int) -> PullRequest:
        """
        Get a pull request from the given repository

        Args:
            repo_name: name of the repository in format {owner}/{repo}
            number: pull request number

        Returns:
            an Issue object
        """
        repo = self._client.get_repo(repo_name)
        return repo.get_pull(number)

    @function
    def star(self, repo: str):
        """
        Star a repository on GitHub.

        Args:
            repo: Name of the repository in format {owner}/{repo}
        """
        repo = self._client.get_repo(repo)
        user = self._client.get_user()
        user.add_to_starred(repo)

        return f"Starred {repo} on behalf of {user.login}"

    @function
    def fork(self, repo: str):
        """
        Fork a repository on GitHub.

        Args:
            repo: Name of the repository in format {owner}/{repo}
        """
        repo = self._client.get_repo(repo)
        user = self._client.get_user()
        forked = user.create_fork(repo)

        return f"Forked {repo} to {forked.full_name}"

    @function
    def watch(self, repo: str):
        """
        Subscribe to notifications (a.k.a. watch) for activity in a repository on GitHub.

        Args:
            repo: Name of the repository in format {owner}/{repo}
        """
        repo = self._client.get_repo(repo)
        user = self._client.get_user()
        user.add_to_watched(repo)

        return f"Watched {repo} on behalf of {user.login}"

    @function
    def search_repositories(self, query: str, max_results: int):
        """
        Search for repositories on GitHub.

        Args:
            query: Search query to search for GitHub repositories. Below are some query examples:
                1. Search for all repositories that contain "test" and use Python: `test language:python`
                2. Search for repositories with more than 1000 stars: `stars:>1000`
            max_results: Maximum number of results to return
        """
        res = self._client.search_repositories(query)

        results = []

        for repo in res[:max_results]:
            results.append(
                {
                    "name": repo.full_name,
                    "owner": repo.owner.login,
                    "url": repo.url,
                    "description": repo.description,
                    "topics": repo.topics,
                    "created_at": repo.created_at.isoformat(),
                    "updated_at": repo.updated_at.isoformat(),
                }
            )

        return json.dumps(results, ensure_ascii=False)

    @function
    def search_issue_pr(self, query: str, max_results: int):
        """
        Search for issues or pull requests on GitHub.

        Args:
            query: Search query to search for GitHub issues and pull requests. Below are some query examples:
                1. Search for all issues containing "performance" in the repository npi/npi: `is:issue repo:npi/npi performance`
                2. Search for open pull requests in repository npi/npi: `is:pr is:open repo:npi/npi`
            max_results: Maximum number of results to return
        """
        res = self._client.search_issues(query=query, sort="created")

        if res.totalCount == 0:
            return "No results found"

        results = []

        for item in res[:max_results]:
            results.append(self._issue_pr_to_json(item))

        return json.dumps(results, ensure_ascii=False)

    @function
    def get_issue(self, repo: str, number: int):
        """
        Get an issue from the given repository.

        Args:
            repo: Name of the repository in format {owner}/{repo}
            number: Issue number
        """
        issue = self._get_issue(repo_name=repo, number=number)
        return json.dumps(self._issue_pr_to_json(issue), ensure_ascii=False)

    @function
    def get_pull_request(self, repo: str, number: int):
        """
        Get a pull request from the given repository.

        Args:
            repo: Name of the repository in format {owner}/{repo}
            number: Pull request number
        """
        pr = self._get_pull_request(repo_name=repo, number=number)
        return json.dumps(self._issue_pr_to_json(pr), ensure_ascii=False)

    @function
    def create_issue(
        self,
        repo: str,
        title: str,
        body: str,
        labels: List[str] = None,
        assignees: List[str] = None,
    ):
        """
        Create an issue under the given repository.

        Args:
            repo: Name of the repository in format {owner}/{repo}
            title: Title of the issue
            body: Body of the issue in markdown format
            labels: List of labels to add to the issue
            assignees: List of users to assign to the issue
        """
        repository = self._client.get_repo(repo)
        issue = repository.create_issue(
            title=title,
            body=body,
            labels=_default_not_set(labels),
            assignees=_default_not_set(assignees),
        )

        return "Issue created:\n" + json.dumps(
            self._issue_pr_to_json(issue), ensure_ascii=False
        )

    @function
    def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        base: str,
        head: str,
        is_draft: bool = False,
        labels: List[str] = None,
        assignees: List[str] = None,
    ):
        """
        Create a pull request under the given repository.

        Args:
            repo: Name of the repository in format {owner}/{repo}
            title: Title of the pull request
            body: Body of the pull request
            base: Base branch of the pull request, i.e., the branch to merge the pull request into
            head: Head branch of the pull request, i.e., the branch with your changes
            is_draft: Whether the pull request is a draft or not
            labels: List of labels to add to the pull request
            assignees: List of users to assign to the pull request
        """
        repository = self._client.get_repo(repo)
        pr = repository.create_pull(
            base=base,
            title=title,
            body=body,
            head=head,
            draft=is_draft,
        )

        if labels:
            pr.add_to_labels(*labels)

        if assignees:
            pr.add_to_assignees(*assignees)

        return "Pull Request created:\n" + json.dumps(
            self._issue_pr_to_json(pr), ensure_ascii=False
        )

    @function
    def add_issue_comment(self, repo: str, number: int, body: str):
        """
        Add a comment to the target issue.

        Args:
            repo: Name of the repository in format {owner}/{repo}
            number: Issue number
            body: Body of the comment in markdown format
        """
        issue = self._get_issue(repo_name=repo, number=number)
        comment = issue.create_comment(body)

        return "Issue comment created:\n" + json.dumps(
            self._comment_to_json(comment), ensure_ascii=False
        )

    @function
    def add_pull_request_comment(self, repo: str, number: int, body: str):
        """
        Add a comment to the target pull request.

        Args:
            repo: Name of the repository in format {owner}/{repo}
            number: Pull request number
            body: Body of the comment in markdown format
        """
        pr = self._get_pull_request(repo_name=repo, number=number)
        comment = pr.create_issue_comment(body)

        return "Issue comment created:\n" + json.dumps(
            self._comment_to_json(comment), ensure_ascii=False
        )

    @function
    def edit_issue(
        self,
        repo: str,
        number: int,
        title: str = None,
        body: str = None,
        labels: List[str] = None,
        assignees: List[str] = None,
        state: Literal["open", "closed"] = None,
    ):
        """
        Edit an existing issue. You can also close or reopen an issue by specifying the state parameter.

        Args:
            repo: Name of the repository in format {owner}/{repo}
            number: Issue number
            title: Title of the issue
            body: Body of the issue in markdown format
            labels: List of labels to add to the issue
            assignees: List of users to assign to the issue
            state: Whether the issue is open or closed
        """
        issue = self._get_issue(repo_name=repo, number=number)

        issue.edit(
            title=_default_not_set(title),
            body=_default_not_set(body),
            labels=_default_not_set(labels),
            assignees=_default_not_set(assignees),
            state=_default_not_set(state),
        )

        return "Issue updated to:\n" + json.dumps(
            self._issue_pr_to_json(issue), ensure_ascii=False
        )

    @function
    def edit_pull_request(
        self,
        repo: str,
        number: int,
        title: str = None,
        body: str = None,
        base: str = None,
        labels: List[str] = None,
        assignees: List[str] = None,
        state: Literal["open", "closed"] = None,
    ):
        """
        Edit an existing pull request. You can also close or reopen a pull request by specifying the state parameter.

        Args:
            repo: Name of the repository in format {owner}/{repo}
            number: Pull request number
            title: Title of the pull request
            body: Body of the pull request in markdown format
            base: Base branch of the pull request, i.e., the branch with your changes
            labels: List of labels to add to the pull request
            assignees: List of users to assign to the pull request
            state: Whether the pull request is open or closed
        """
        pr = self._get_pull_request(repo_name=repo, number=number)

        pr.edit(
            title=_default_not_set(title),
            body=_default_not_set(body),
            state=_default_not_set(state),
            base=_default_not_set(base),
        )

        if labels:
            pr.add_to_labels(*labels)

        if assignees:
            pr.add_to_assignees(*assignees)

        return "Pull Request updated to:\n" + json.dumps(
            self._issue_pr_to_json(pr), ensure_ascii=False
        )
