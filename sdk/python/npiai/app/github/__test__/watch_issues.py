import asyncio

from npiai.core import create_agent
from npiai.app.github import GitHub


async def main():
    async with create_agent(GitHub()) as github:
        return await github.chat('Notify me when new issues are created in idiotWu/npi-test')


if __name__ == '__main__':
    asyncio.run(main())
