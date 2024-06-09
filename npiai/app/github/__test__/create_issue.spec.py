import asyncio

from npiai import agent_wrapper
from npiai import GitHub


async def main():
    async with agent_wrapper(GitHub()) as github:
        return await github.chat('Create a test issue in idiotWu/npi-test with label "NPi" and assign it to @idiotWu')


if __name__ == '__main__':
    asyncio.run(main())
