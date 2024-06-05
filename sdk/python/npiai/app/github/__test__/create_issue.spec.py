import asyncio

from npiai.core import create_agent
from npiai.app.github import GitHub


async def main():
    async with create_agent(GitHub()) as github:
        return await github.chat('Create a test issue in idiotWu/npi-test with label "NPi" and assign it to @idiotWu')


if __name__ == '__main__':
    asyncio.run(main())
