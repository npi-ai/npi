import asyncio
from npiai.core import create_agent
from npiai.browser_app.twitter import Twitter


async def main():
    async with create_agent(Twitter(headless=False)) as twitter:
        return await twitter.chat(
            'Find the latest 10 tweets by @AtomSilverman. You should also include the link to the tweet. You must try to load more tweets until exactly 10 tweets are found. Output all tweets in your final response.'
        )


if __name__ == '__main__':
    asyncio.run(main())