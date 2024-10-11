import asyncio
from npiai import agent
from npiai.tools.web.scraper import Scraper
from npiai.utils.test_utils import DebugContext


async def main():
    async with agent.wrap(Scraper(headless=False)) as tool:
        return await tool.chat(
            DebugContext(),
            """
            Summarize the content of the following webpage into a table:
            
            - URL: https://www.bardeen.ai/playbooks
            - Ancestor Selector: .playbook_list
            - Items Selector: .playbook_list .playbook_item-link
            - Output Columns: ["Apps Name", "Description", "Category" , "Time Saved"]
            - Limit: 128
            """,
        )


if __name__ == "__main__":
    asyncio.run(main())
