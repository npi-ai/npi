import os
import asyncio
from npiai import agent
from npiai.utils.test_utils import DebugContext
from npiai.tools.web.twitter import Twitter, TwitterClient


async def main():
    ctx = DebugContext()

    client = TwitterClient(
        ctx=ctx,
        username=os.environ.get("TWITTER_USERNAME"),
        password=os.environ.get("TWITTER_PASSWORD"),
        headless=False,
    )

    async with agent.wrap(Twitter(client=client, headless=False)) as twitter:
        return await twitter.chat(
            ctx,
            "Find the latest 10 tweets by @AtomSilverman. You should also include the link to the tweet. You must try to load more tweets until exactly 10 tweets are found. Output all tweets in your final response.",
        )


if __name__ == "__main__":
    asyncio.run(main())
