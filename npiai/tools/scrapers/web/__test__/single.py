import asyncio
import json

from npiai.tools.scrapers.web import WebScraper
from npiai.utils.test_utils import DebugContext


async def main():
    async with WebScraper(
        headless=False,
        url="https://www.bardeen.ai/playbooks/get-data-from-the-currently-opened-imdb-com-title-page",
        scraping_type="single",
    ) as scraper:
        columns = await scraper.infer_columns(
            ctx=DebugContext(),
        )
        print("Inferred columns:", json.dumps(columns, indent=2))

        stream = scraper.summarize_stream(
            ctx=DebugContext(),
            output_columns=columns,
            limit=1,
        )

        async for items in stream:
            print("Chunk:", json.dumps(items, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
