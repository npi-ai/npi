from npiai import BrowserApp, function, NavigatorAgent
from npiai import LLM

__SYSTEM_PROMPT__ = """
You are a general browser-based autonomous agent helping user to finish any task on any webpage. For a given task, you should first go to the appropriate web page, and then pass the task to the navigator to fulfill it.
"""


class Browser(BrowserApp):
    def __init__(self, navigator_llm: LLM = None, headless: bool = True):
        super().__init__(
            name='browser',
            description='Perform any task on any webpage',
            system_prompt=__SYSTEM_PROMPT__,
            headless=headless,
        )

        self.add(
            NavigatorAgent(
                llm=navigator_llm,
                playwright=self.playwright,
            )
        )

    @function
    async def goto(self, url: str):
        """
        Open the given URL in the browser.

        Args:
            url: The URL to open.
        """
        await self.playwright.page.goto(url)

        return f'Opened {await self.get_page_url()}, page title: {await self.get_page_title()}'
