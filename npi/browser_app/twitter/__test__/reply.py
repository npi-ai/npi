import asyncio
from npi.browser_app.twitter import Twitter


async def main():
    twitter = Twitter(headless=False)
    await twitter.chat(
        'Reply to the latest tweet of @elonmusk with your opinions. You can write anything you like.',
    )


if __name__ == '__main__':
    asyncio.run(main())
