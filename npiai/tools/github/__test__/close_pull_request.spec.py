import asyncio

from npiai import agent
from npiai.tools import GitHub


async def main():
    async with agent.wrap(GitHub()) as github:
        return await github.chat("Close all pull requests in idiotWu/npi-test")


if __name__ == "__main__":
    asyncio.run(main())
