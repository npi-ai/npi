import asyncio

from npiai.utils.test_utils import DebugContext

# from npiai import Context
from npiai.tools.web.page_analyzer import PageAnalyzer
from npiai.tools.web.scraper import Scraper
from utils import auto_scrape


async def main():
    url = input("Enter the URL: ")
    # url = "https://www.bardeen.ai/playbooks"

    async with PageAnalyzer(headless=False) as analyzer:
        scraper = Scraper(batch_size=5, playwright=analyzer.playwright)

        await auto_scrape(
            ctx=DebugContext(),
            analyzer=analyzer,
            scraper=scraper,
            url=url,
        )


if __name__ == "__main__":
    asyncio.run(main())
