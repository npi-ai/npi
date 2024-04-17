import asyncio
from npi.browser_app.twitter import Twitter


async def main():
    twitter = Twitter(headless=False)
    await twitter.chat(
        'Post a tweet about "The answer to everything."'
    )


if __name__ == '__main__':
    asyncio.run(main())
