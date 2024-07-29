import asyncio
from npiai import agent
from npiai.tools.web import Twitter


async def main():
    async with agent.wrap(Twitter(headless=False)) as twitter:
        return await twitter.chat(
            "Find the latest 10 tweets by @AtomSilverman. You should also include the link to the tweet. You must try to load more tweets until exactly 10 tweets are found. Output all tweets in your final response."
        )


if __name__ == "__main__":
    asyncio.run(main())
