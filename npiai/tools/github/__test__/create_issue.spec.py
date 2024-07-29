import asyncio

from npiai import agent
from npiai.tools import GitHub


async def main():
    async with agent.wrap(GitHub()) as github:
        return await github.chat(
            'Create a test issue in idiotWu/npi-test with label "NPi" and assign it to @idiotWu'
        )


if __name__ == "__main__":
    asyncio.run(main())
