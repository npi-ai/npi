import asyncio

from npiai.core import create_agent
from npiai.app.github import GitHub


async def main():
    async with create_agent(GitHub()) as github:
        return await github.chat('Star and fork npi-ai/npi')


if __name__ == '__main__':
    asyncio.run(main())