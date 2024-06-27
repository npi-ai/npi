import asyncio

from npi.app.github import GitHub
from utils import test_init_github_cred


async def main():
    github = GitHub()
    return await github.chat(
        'Find the issue in the repo idiotWu/npi-test titled "Test Issue for NPi" and change the body to "Hello World"'
    )


if __name__ == '__main__':
    test_init_github_cred()
    asyncio.run(main())
