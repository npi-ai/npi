import asyncio
import json

from npiai.tools.web.scraper import Scraper
from npiai.utils.test_utils import DebugContext

# from npiai.context import Context


async def main():
    async with Scraper(headless=False, batch_size=10) as scraper:
        stream = scraper.summarize_stream(
            ctx=DebugContext(),
            url="https://www.bardeen.ai/playbooks",
            scraping_type="list-like",
            ancestor_selector=".playbook_list",
            items_selector=".playbook_list .playbook_item-link",
            limit=42,
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

        async for chunk in stream:
            print("Chunk:", json.dumps(chunk, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
