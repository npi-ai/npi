import asyncio
import json

from npiai.tools.scrapers.web import WebScraper
from npiai.utils.test_utils import DebugContext

url = "https://www.bardeen.ai/playbooks"
ancestor_selector = ".playbook_list"
items_selector = ".playbook_list .playbook_item-link"


async def main():
    async with WebScraper(
        headless=False,
        scraping_type="list-like",
        url="https://www.bardeen.ai/playbooks",
        ancestor_selector=".playbook_list",
        items_selector=".playbook_list .playbook_item-link",
    ) as scraper:
        columns = await scraper.infer_columns(
            ctx=DebugContext(),
        )

        print("Inferred columns:", json.dumps(columns, indent=2))

        stream = scraper.summarize_stream(
            ctx=DebugContext(),
            limit=10,
            batch_size=5,
            output_columns=columns,
        )

        async for items in stream:
            print("Chunk:", json.dumps(items, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
