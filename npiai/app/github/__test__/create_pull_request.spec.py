import asyncio

from npiai import agent_wrapper
from npiai import GitHub


async def main():
    async with agent_wrapper(GitHub()) as github:
        return await github.chat(
            'Create a pull request in idiotWu/npi-test from "npi-test" branch to "main" branch with random title and body'
        )


if __name__ == '__main__':
    asyncio.run(main())
