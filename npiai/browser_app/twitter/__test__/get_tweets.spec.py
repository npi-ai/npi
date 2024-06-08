import asyncio
from npiai import create_agent
from npiai.browser_app import Twitter


async def main():
    async with create_agent(Twitter(headless=False)) as twitter:
        return await twitter.chat(
            'Find and summarize the latest tweet by @AtomSilverman discussing AI agents. You should also include the link to the tweet.'
        )


if __name__ == '__main__':
    asyncio.run(main())
