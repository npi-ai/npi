import json
from github import Github as PyGithub, Auth
from github.IssueComment import IssueComment
from github.Issue import Issue
from github.PullRequestComment import PullRequestComment
from github.PullRequest import PullRequest
from github.GithubObject import NotSet
from typing import Union, TypeVar

from npi.core import App, npi_tool
from npi.config import config
from npi.error.auth import UnauthorizedError
from .schema import *

_T = TypeVar('_T')


def _default_not_set(value: _T) -> _T | 'NotSet':
    return value if value is not None else NotSet


# TODO: PR review
class GitHub(App):
    github_client: PyGithub

    def __init__(self, llm=None):
        cred = config.get_github_credentials()

        if cred is None:
            raise UnauthorizedError("GitHub credentials are not found, please use `npi auth github` first")

        super().__init__(
            name='github',
            description='Manage GitHub issues and pull requests using English, e.g., github("reply to the latest '
                        'issue in npi/npi")',
            system_role='You are a GitHub Agent helping users to manage their issues and pull requests',
            llm=llm,
        )

        self.github_client = PyGithub(auth=Auth.Token(cred.access_token))

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
            'id': comment.id,
            'created_at': comment.created_at.isoformat(),
            'updated_at': comment.updated_at.isoformat(),
            'author': comment.user.login,
            'body': comment.body,
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
            'number': issue_or_pr.number,
            'title': issue_or_pr.title,
            'created_at': issue_or_pr.created_at.isoformat(),
            'updated_at': issue_or_pr.updated_at.isoformat(),
            'is_closed': issue_or_pr.closed_at is not None,
            'author': issue_or_pr.user.login,
            'body': issue_or_pr.body,
            'comments_count': issue_or_pr.comments,
            'assignees': [user.login for user in issue_or_pr.assignees],
            'labels': [label.name for label in issue_or_pr.labels],
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
        repo = self.github_client.get_repo(repo_name)
        return repo.get_issue(number)

    def _get_pull_request(self, repo_name: str, number: int) -> PullRequest:
        """
        Get a pull request from the given repository

        Args:
            repo_name: name of the repository in format {owner}/{repo}
            number: pull request number

        Returns:
            an Issue object
        """
        repo = self.github_client.get_repo(repo_name)
        return repo.get_pull(number)

    @npi_tool
    def star(self, params: StarParameters):
        """Star a repository on GitHub"""
        repo = self.github_client.get_repo(params.repo)
        user = self.github_client.get_user()
        user.add_to_starred(repo)

        return f'Starred {params.repo} on behalf of {user.login}'

    @npi_tool
    def fork(self, params: ForkParameters):
        """Fork a repository on GitHub"""
        repo = self.github_client.get_repo(params.repo)
        user = self.github_client.get_user()
        forked = user.create_fork(repo)

        return f'Forked {params.repo} to {forked.full_name}'

    @npi_tool
    def watch(self, params: WatchParameters):
        """Watch a repository on GitHub"""
        repo = self.github_client.get_repo(params.repo)
        user = self.github_client.get_user()
        user.add_to_watched(repo)

        return f'Watched {params.repo} on behalf of {user.login}'

    @npi_tool
    def search_repositories(self, params: SearchRepositoriesParameters):
        """Search for repositories on GitHub"""
        res = self.github_client.search_repositories(params.query)

        results = []

        for repo in res[:params.max_results]:
            results.append(
                {
                    'name': repo.full_name,
                    'owner': repo.owner.login,
                    'url': repo.url,
                    'description': repo.description,
                    'topics': repo.topics,
                    'created_at': repo.created_at.isoformat(),
                    'updated_at': repo.updated_at.isoformat(),
                }
            )

        return json.dumps(results, ensure_ascii=False)

    @npi_tool
    def search_issue_pr(self, params: SearchIssuePRParameters):
        """Search for issues or pull requests on GitHub"""
        res = self.github_client.search_issues(query=params.query, sort='created')

        if res.totalCount == 0:
            return 'No results found'

        return json.dumps([self._issue_pr_to_json(item) for item in res], ensure_ascii=False)

    @npi_tool
    def get_issue(self, params: GetIssueParameters):
        """Get an issue from the given repository"""
        issue = self._get_issue(repo_name=params.repository, number=params.number)
        return json.dumps(self._issue_pr_to_json(issue), ensure_ascii=False)

    @npi_tool
    def get_pull_request(self, params: GetPullRequestParameters):
        """Get a pull request from the given repository"""
        pr = self._get_pull_request(repo_name=params.repository, number=params.number)
        return json.dumps(self._issue_pr_to_json(pr), ensure_ascii=False)

    @npi_tool
    def create_issue(self, params: CreateIssueParameters):
        """Create an issue under the given repository"""
        repo = self.github_client.get_repo(params.repository)
        issue = repo.create_issue(
            title=params.title,
            body=params.body,
            labels=_default_not_set(params.labels),
            assignees=_default_not_set(params.assignees),
        )

        return 'Issue created:\n' + json.dumps(self._issue_pr_to_json(issue), ensure_ascii=False)

    @npi_tool
    def create_pull_request(self, params: CreatePullRequestParameters):
        """Create a pull request under the given repository"""
        repo = self.github_client.get_repo(params.repository)
        pr = repo.create_pull(
            base=params.base,
            title=params.title,
            body=params.body,
            head=params.head,
            draft=params.is_draft,
        )

        if params.labels:
            pr.add_to_labels(*params.labels)

        if params.assignees:
            pr.add_to_assignees(*params.assignees)

        return 'Pull Request created:\n' + json.dumps(self._issue_pr_to_json(pr), ensure_ascii=False)

    @npi_tool
    def add_issue_comment(self, params: AddIssueCommentParameters):
        """Add a comment to the target issue"""
        issue = self._get_issue(repo_name=params.repository, number=params.number)
        comment = issue.create_comment(params.body)

        return 'Issue comment created:\n' + json.dumps(self._comment_to_json(comment), ensure_ascii=False)

    @npi_tool
    def add_pull_request_comment(self, params: AddPullRequestCommentParameters):
        """Add a comment to the target pull request"""
        pr = self._get_pull_request(repo_name=params.repository, number=params.number)
        comment = pr.create_issue_comment(params.body)

        return 'Issue comment created:\n' + json.dumps(self._comment_to_json(comment), ensure_ascii=False)

    @npi_tool
    def edit_issue(self, params: EditIssueParameters):
        """Edit an existing issue. You can also close or reopen an issue by specifying the state parameter."""
        issue = self._get_issue(repo_name=params.repository, number=params.number)

        issue.edit(
            title=_default_not_set(params.title),
            body=_default_not_set(params.body),
            labels=_default_not_set(params.labels),
            assignees=_default_not_set(params.assignees),
            state=_default_not_set(params.state),
        )

        return 'Issue updated to:\n' + json.dumps(self._issue_pr_to_json(issue), ensure_ascii=False)

    @npi_tool
    def edit_pull_request(self, params: EditPullRequestParameters):
        """Edit an existing pull request. You can also close or reopen a pull request by specifying the state parameter."""
        pr = self._get_pull_request(repo_name=params.repository, number=params.number)

        pr.edit(
            title=_default_not_set(params.title),
            body=_default_not_set(params.body),
            state=_default_not_set(params.state),
            base=_default_not_set(params.base),
        )

        if params.labels:
            pr.add_to_labels(params.labels)

        if params.assignees:
            pr.add_to_assignees(params.assignees)

        return 'Pull Request updated to:\n' + json.dumps(self._issue_pr_to_json(pr), ensure_ascii=False)
