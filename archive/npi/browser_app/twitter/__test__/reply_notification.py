import asyncio
from npi.browser_app.twitter import Twitter
from utils import test_init_twitter_cred


async def main():
    twitter = Twitter(headless=False)
    await twitter.chat(
        'Reply to the latest message in the notifications with your opinions. You can write anything you like.',
    )


if __name__ == '__main__':
    test_init_twitter_cred()
    asyncio.run(main())
