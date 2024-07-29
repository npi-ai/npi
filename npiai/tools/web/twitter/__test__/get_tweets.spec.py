import asyncio
from npiai import agent
from npiai.tools.web import Twitter


async def main():
    async with agent.wrap(Twitter(headless=False)) as twitter:
        return await twitter.chat(
            "Find and summarize the latest tweet by @AtomSilverman discussing AI agents. You should also include the link to the tweet."
        )


if __name__ == "__main__":
    asyncio.run(main())
