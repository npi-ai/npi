import asyncio
from npiai import agent
from npiai.tools.web import Twitter


async def main():
    async with agent.wrap(Twitter(headless=False)) as twitter:
        return await twitter.chat(
            "Reply to the latest tweet of @elonmusk with your opinions. You can write anything you like.",
        )


if __name__ == "__main__":
    asyncio.run(main())
