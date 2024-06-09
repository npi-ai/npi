import asyncio
from npiai import agent_wrapper
from npiai.browser_app import Twitter


async def main():
    async with agent_wrapper(Twitter(headless=False)) as twitter:
        return await twitter.chat(
            'Post a tweet about "The answer to everything."'
        )


if __name__ == '__main__':
    asyncio.run(main())
