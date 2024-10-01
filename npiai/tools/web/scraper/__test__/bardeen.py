import asyncio
from npiai import agent, Context
from npiai.types import RuntimeMessage
from npiai.utils import logger
from npiai.tools.web.scraper import Scraper


class DebugContext(Context):
    async def send(self, msg: RuntimeMessage):
        if msg["type"] == "screenshot":
            return
        logger.debug(msg["message"] if "message" in msg else msg)


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
