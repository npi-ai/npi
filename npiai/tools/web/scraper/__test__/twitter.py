import asyncio

# from npiai.utils.test_utils import DebugContext
from npiai import Context
from npiai.tools.web.page_analyzer import PageAnalyzer
from npiai.tools.web.scraper import Scraper
from npiai.tools.web.twitter import Twitter
from utils import auto_scrape


async def main():
    async with Twitter(headless=False) as twitter:
        await auto_scrape(
            ctx=Context(),
            analyzer=PageAnalyzer(playwright=twitter.playwright),
            scraper=Scraper(batch_size=10, playwright=twitter.playwright),
            url="https://x.com/home",
        )


if __name__ == "__main__":
    asyncio.run(main())
