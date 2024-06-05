import asyncio

from npiai.core import create_agent
from npiai.app.github import GitHub


async def main():
    async with create_agent(GitHub()) as github:
        return await github.chat('Close all pull requests in idiotWu/npi-test')


if __name__ == '__main__':
    asyncio.run(main())
