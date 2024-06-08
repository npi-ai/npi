import asyncio
from npiai import create_agent
from npiai.browser_app import Twitter


async def main():
    async with create_agent(Twitter(headless=False)) as twitter:
        return await twitter.chat(
            'Post a tweet about "The answer to everything."'
        )


if __name__ == '__main__':
    asyncio.run(main())
