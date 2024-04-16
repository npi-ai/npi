from openai import AsyncOpenAI

from npi.core import BrowserApp, npi_tool
from .schema import *

__SYSTEM_PROMPT__ = """
You are a general browser-based autonomous agent helping user to finish any task on any webpage. For a given task, you should first go to the appropriate web page, and then pass the task to the navigator to fulfill it.
"""


class GeneralBrowserAgent(BrowserApp):
    def __init__(self, llm=None, headless: bool = True):
        if not llm:
            llm = AsyncOpenAI()

        super().__init__(
            name='general-browser-agent',
            description='Perform any task on any webpage',
            system_role=__SYSTEM_PROMPT__,
            llm=llm,
            headless=headless,
            use_navigator=True,
        )

    @npi_tool
    async def goto(self, params: GotoParameters):
        """Open the given URL in the browser"""
        await self.page.goto(params.url)
        # self.page.wait_for_url(params.url)

        return f'Opened {self.page.url}, page title: {self.page.title}'
