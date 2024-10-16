import asyncio
from npiai.tools.web.scraper import Scraper
from npiai.utils.test_utils import DebugContext


async def main():
    async with Scraper(headless=False, batch_size=10) as scraper:
        await scraper.summarize(
            ctx=DebugContext(),
            url="https://www.bardeen.ai/playbooks",
            ancestor_selector=".playbook_list",
            items_selector=".playbook_list .playbook_item-link",
            output_columns=["Apps Name", "Description", "Category", "Time Saved"],
            limit=42,
        )


if __name__ == "__main__":
    asyncio.run(main())
