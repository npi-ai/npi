import asyncio
from npi.browser_app.twitter import Twitter
from utils import test_init_twitter_cred


async def main():
    twitter = Twitter(headless=False)
    await twitter.chat(
        'Post a tweet about "The answer to everything."'
    )


if __name__ == '__main__':
    test_init_twitter_cred()
    asyncio.run(main())
