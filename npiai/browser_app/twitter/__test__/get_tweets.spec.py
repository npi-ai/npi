import asyncio
from npiai import agent_wrapper
from npiai.browser_app import Twitter


async def main():
    async with agent_wrapper(Twitter(headless=False)) as twitter:
        return await twitter.chat(
            'Find and summarize the latest tweet by @AtomSilverman discussing AI agents. You should also include the link to the tweet.'
        )


if __name__ == '__main__':
    asyncio.run(main())
