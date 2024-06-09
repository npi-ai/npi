import asyncio

from npiai import agent_wrapper
from npiai import GitHub


async def main():
    async with agent_wrapper(GitHub()) as github:
        return await github.chat('Close all pull requests in idiotWu/npi-test')


if __name__ == '__main__':
    asyncio.run(main())
