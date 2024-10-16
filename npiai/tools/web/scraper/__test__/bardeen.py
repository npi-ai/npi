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
            output_file=".cache/bardeen.csv",
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
            limit=42,
        )


if __name__ == "__main__":
    asyncio.run(main())
