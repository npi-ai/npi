import asyncio
import json
import time

from npiai.tools.scrapers.web import WebScraper
from npiai.utils.test_utils import DebugContext

# from npiai.context import Context


async def main():
    async with WebScraper(
        headless=False,
        url="https://www.bardeen.ai/playbooks",
        scraping_type="list-like",
        ancestor_selector=".playbook_list",
        items_selector=".playbook_list .playbook_item",
    ) as scraper:
        stream = scraper.summarize_stream(
            ctx=DebugContext(),
            limit=100,
            batch_size=5,
            concurrency=10,
            output_columns=[
                {
                    "name": "Apps Involved",
                    "description": "The apps involved in the playbook",
                },
                {
                    "name": "Description",
                    "description": "The description of the playbook",
                },
                {
                    "name": "Time Saved",
                    "description": "The time saved by using the playbook",
                },
                {
                    "name": "URL",
                    "description": "The URL of the playbook",
                },
            ],
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
