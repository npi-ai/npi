import asyncio

from npi.app.github import GitHub
from utils import test_init_github_cred


async def main():
    github = GitHub()
    return await github.chat(
        'Create a pull request in idiotWu/npi-test from "npi-test" branch to "main" branch with random title and body'
    )


if __name__ == '__main__':
    test_init_github_cred()
    asyncio.run(main())
