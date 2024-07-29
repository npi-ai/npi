import asyncio
from npiai import agent
from npiai.tools.web import Twitter


async def main():
    async with agent.wrap(Twitter(headless=False)) as twitter:
        return await twitter.chat('Post a tweet about "The answer to everything."')


if __name__ == "__main__":
    asyncio.run(main())
