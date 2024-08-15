from npiai.core import NavigatorAgent
from npiai import LLM, function, BrowserTool, Context, utils

__SYSTEM_PROMPT__ = """
You are a general chromium-based autonomous agent helping user to finish any task on any webpage. For a given task,
 you should first go to the appropriate web page, and then pass the task to the navigator to fulfill it.
"""


class Chromium(BrowserTool):
    name = "chrome"
    description = "Perform any task on any webpage"
    system_prompt = __SYSTEM_PROMPT__

    def __init__(self, navigator_llm: LLM = None, headless: bool = True):
        super().__init__(
            headless=headless,
        )
        self.add_tool(
            NavigatorAgent(
                llm=navigator_llm,
                playwright=self.playwright,
            )
        )

    @classmethod
    def from_context(cls, ctx: Context) -> "Chromium":
        if not utils.is_cloud_env():
            raise RuntimeError(
                "Chromium tool can only be initialized from context in the NPi cloud environment"
            )
        return cls()

    @function
    async def goto(self, url: str):
        """
        Open the given URL in chromium.

        Args:
            url: The URL to open.
        """
        await self.playwright.page.goto(url)

        return f"Opened {await self.get_page_url()}, page title: {await self.get_page_title()}"
