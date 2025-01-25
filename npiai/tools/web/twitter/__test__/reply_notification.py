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

    async with agent.wrap(Twitter(client=client)) as twitter:
        return await twitter.chat(
            ctx,
            "Reply to the latest message in the notifications with your opinions. You can write anything you like.",
        )


if __name__ == "__main__":
    asyncio.run(main())
