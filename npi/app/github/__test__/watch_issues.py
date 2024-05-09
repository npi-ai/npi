import asyncio

from npi.app.github import GitHub
from utils import test_init_github_cred


async def main():
    github = GitHub()
    return await github.chat('Notify me when new issues are created in idiotWu/npi-test')


if __name__ == '__main__':
    test_init_github_cred()
    asyncio.run(main())
