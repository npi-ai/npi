import asyncio
import json
import time
from typing import Set

from npiai.tools.web.scraper import Scraper
from npiai.utils.test_utils import DebugContext

# from npiai.context import Context


async def summarize(skip_item_hashes: Set[str] | None = None):
    async with Scraper(headless=False, batch_size=5) as scraper:
        stream = scraper.summarize_stream(
            ctx=DebugContext(),
            url="https://www.bardeen.ai/playbooks",
            scraping_type="list-like",
            ancestor_selector=".playbook_list",
            items_selector=".playbook_list .playbook_item",
            limit=20,
            concurrency=2,
            skip_item_hashes=skip_item_hashes,
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
        hashes = set()
        matched_hashes = set()

        async for chunk in stream:
            count += len(chunk["items"])
            print("Chunk:", json.dumps(chunk, indent=2))
            matched_hashes.update(chunk["matched_hashes"])

            for item in chunk["items"]:
                hashes.add(item["hash"])

        end = time.monotonic()
        print(f"Summarized {count} items in {end - start:.2f} seconds")

        if skip_item_hashes:
            print("Matched hashes:", matched_hashes)
            print("Unmatched hashes:", skip_item_hashes - matched_hashes)

        return hashes


async def main():
    hashes = await summarize()
    await summarize(hashes)


if __name__ == "__main__":
    asyncio.run(main())
