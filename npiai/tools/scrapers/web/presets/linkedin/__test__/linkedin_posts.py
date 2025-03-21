import asyncio
import json
import time

from npiai.tools.scrapers.web.presets.linkedin import LinkedinPostsScraper
from npiai.utils.test_utils import DebugContext
from npiai import Context


async def main():
    async with LinkedinPostsScraper(
        headless=False,
        url="https://www.linkedin.com/in/jerry-liu-64390071/recent-activity/all/",
    ) as scraper:
        stream = scraper.scrape_posts_stream(
            ctx=DebugContext(),
            limit=100,
            concurrency=10,
        )

        start = time.monotonic()
        count = 0

        async for chunk in stream:
            count += len(chunk["items"])
            print("Chunk:", json.dumps(chunk, indent=2))

        end = time.monotonic()
        print(f"Summarized {count} items in {end - start:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
