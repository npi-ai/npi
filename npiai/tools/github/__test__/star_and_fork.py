import asyncio

from npiai import agent
from npiai.tools import GitHub


async def main():
    async with agent.wrap(GitHub()) as github:
        return await github.chat("Star and fork npi-ai/npi")


if __name__ == "__main__":
    asyncio.run(main())
