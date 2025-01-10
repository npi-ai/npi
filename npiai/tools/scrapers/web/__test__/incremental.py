import asyncio
import json
import time
from typing import List

from npiai.tools.scrapers.web import WebScraper
from npiai.utils.test_utils import DebugContext

# from npiai.context import Context


async def summarize(skip_item_hashes: List[str] | None = None):
    async with WebScraper(
        headless=False,
        url="https://www.bardeen.ai/playbooks",
        scraping_type="list-like",
        ancestor_selector=".playbook_list",
        items_selector=".playbook_list .playbook_item",
        skip_item_hashes=skip_item_hashes,
    ) as scraper:
        stream = scraper.summarize_stream(
            ctx=DebugContext(),
            limit=2,
            batch_size=2,
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
        hashes = []

        async for chunk in stream:
            count += len(chunk["items"])
            print("Chunk:", json.dumps(chunk, indent=2))

            for item in chunk["items"]:
                hashes.append(item["hash"])

        end = time.monotonic()
        print(f"Summarized {count} items in {end - start:.2f} seconds")

        if skip_item_hashes:
            matched_hashes = set(scraper.get_matched_hashes())
            print("Matched hashes:", matched_hashes)
            print("Unmatched hashes:", set(skip_item_hashes) - matched_hashes)

        return hashes


async def main():
    hashes = await summarize()
    await summarize(hashes)


if __name__ == "__main__":
    asyncio.run(main())
