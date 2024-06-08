import asyncio

from npiai import create_agent
from npiai import GitHub


async def main():
    async with create_agent(GitHub()) as github:
        return await github.chat(
            'Find the issue in the repo idiotWu/npi-test titled "Test Issue for NPi" and change the body to "Hello World"'
        )


if __name__ == '__main__':
    asyncio.run(main())
