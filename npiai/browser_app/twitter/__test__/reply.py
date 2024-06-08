import asyncio
from npiai import create_agent
from npiai.browser_app import Twitter


async def main():
    async with create_agent(Twitter(headless=False)) as twitter:
        return await twitter.chat(
            'Reply to the latest tweet of @elonmusk with your opinions. You can write anything you like.',
        )


if __name__ == '__main__':
    asyncio.run(main())
