import asyncio
import json

from npiai.tools.web.scraper import Scraper
from npiai.utils.test_utils import DebugContext

url = "https://www.amazon.co.jp/dp/B0DHCTRH16/"


async def main():
    async with Scraper(headless=False, batch_size=10) as scraper:
        columns = await scraper.infer_columns(
            ctx=DebugContext(),
            url=url,
            scraping_type="single",
        )

        print("Inferred columns:", json.dumps(columns, indent=2))

        stream = scraper.summarize_stream(
            ctx=DebugContext(),
            url=url,
            scraping_type="single",
            output_columns=columns,
        )

        async for items in stream:
            print("Chunk:", json.dumps(items, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
