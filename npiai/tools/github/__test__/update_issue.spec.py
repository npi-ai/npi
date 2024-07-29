import asyncio

from npiai import agent
from npiai.tools import GitHub


async def main():
    async with agent.wrap(GitHub()) as github:
        return await github.chat(
            'Find the issue in the repo idiotWu/npi-test titled "Test Issue for NPi" and change the body to "Hello World"'
        )


if __name__ == "__main__":
    asyncio.run(main())
