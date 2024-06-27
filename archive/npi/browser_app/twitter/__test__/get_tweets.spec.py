import asyncio
from npi.browser_app.twitter import Twitter
from utils import test_init_twitter_cred


async def main():
    twitter = Twitter(headless=False)
    await twitter.chat(
        'Find and summarize the latest tweet by @AtomSilverman discussing AI agents. You should also include the link to the tweet.'
    )


if __name__ == '__main__':
    test_init_twitter_cred()
    asyncio.run(main())
