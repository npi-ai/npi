import asyncio
from npi.browser_app.twitter import Twitter


async def main():
    twitter = Twitter(headless=False)
    await twitter.chat(
        'Find the latest 10 tweets by @AtomSilverman. You should also include the link to the tweet. You must return exact 10 tweets.'
    )


if __name__ == '__main__':
    asyncio.run(main())
