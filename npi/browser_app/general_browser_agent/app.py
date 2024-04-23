from openai import AsyncOpenAI

from npi.core import BrowserApp, npi_tool
from npi.browser_app.navigator import Navigator
from .schema import *

__SYSTEM_PROMPT__ = """
You are a general browser-based autonomous agent helping user to finish any task on any webpage. For a given task, you should first go to the appropriate web page, and then pass the task to the navigator to fulfill it.
"""


class GeneralBrowserAgent(BrowserApp):
    def __init__(self, llm=None, headless: bool = True):
        super().__init__(
            name='general-browser-agent',
            description='Perform any task on any webpage',
            system_role=__SYSTEM_PROMPT__,
            llm=llm,
            headless=headless,
        )

        self.register(Navigator(playwright=self.playwright))

    @npi_tool
    async def goto(self, params: GotoParameters):
        """Open the given URL in the browser"""
        await self.playwright.page.goto(params.url)
        # self.page.wait_for_url(params.url)

        return f'Opened {await self.get_page_url()}, page title: {await self.get_page_title()}'
