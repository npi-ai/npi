import asyncio
import json

from npiai.tools.web.scraper import Scraper
from npiai.utils.test_utils import DebugContext

url = "https://www.bardeen.ai/playbooks"
ancestor_selector = ".playbook_list"
items_selector = ".playbook_list .playbook_item-link"


async def main():
    async with Scraper(headless=False, batch_size=10) as scraper:
        columns = await scraper.infer_columns(
            ctx=DebugContext(),
            url=url,
            ancestor_selector=ancestor_selector,
            items_selector=items_selector,
        )

        print("Inferred columns:", json.dumps(columns, indent=2))

        await scraper.summarize(
            ctx=DebugContext(),
            url=url,
            ancestor_selector=ancestor_selector,
            items_selector=items_selector,
            output_columns=columns,
            output_file=".cache/bardeen.json",
            limit=10,
        )


if __name__ == "__main__":
    asyncio.run(main())
