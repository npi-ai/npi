import json
import os
import pathlib
import tempfile
from typing import Iterable, AsyncGenerator

from slugify import slugify

from npiai import Context
from npiai.error import UnauthorizedError
from npiai.tools.web.scraper import Scraper
from npiai.tools.web.scraper.types import SummaryChunk
from npiai.utils.html_to_markdown import CompactMarkdownConverter
from .columns import POST_COLUMNS

__ROUTES__ = {
    "login": "https://www.linkedin.com/login/",
    "home": "https://www.linkedin.com/feed/",
}


class LinkedinMarkdownConverter(CompactMarkdownConverter):
    def convert_code(self, el, text, convert_as_inline):
        # omit code blocks
        return ""


class LinkedinScraper(Scraper):
    markdown_converter = LinkedinMarkdownConverter()

    async def start(self):
        await super().start()
        await self._login()

    async def _login(self):
        username = os.environ.get("LINKEDIN_USERNAME", None)
        password = os.environ.get("LINKEDIN_PASSWORD", None)

        if not username:
            raise UnauthorizedError("No LinkedIn username provided")
        if not password:
            raise UnauthorizedError("No LinkedIn password provided")

        state_file = (
            pathlib.Path(tempfile.gettempdir())
            / f"{slugify(username)}/linkedin_state.json"
        )

        if state_file.exists():
            with open(state_file, "r") as f:
                state = json.load(f)
                await self.playwright.context.add_cookies(state["cookies"])

            try:
                # validate cookies
                await self.playwright.page.goto(__ROUTES__["home"])
                await self.playwright.page.wait_for_url(__ROUTES__["home"])
                return
            except TimeoutError:
                pass

        await self.playwright.page.goto(__ROUTES__["login"])
        # fill the login form
        await self.playwright.page.locator("#username").fill(username)
        await self.playwright.page.locator("#password").fill(password)
        await self.playwright.page.locator("button[type='submit']").click()
        # wait for being redirected to the home page
        await self.playwright.page.wait_for_url(__ROUTES__["home"])

        # save the cookies
        save_dir = os.path.dirname(state_file)
        os.makedirs(save_dir, exist_ok=True)
        await self.playwright.context.storage_state(path=state_file)

    async def scrape_posts_stream(
        self,
        ctx: Context,
        url: str,
        limit: int = -1,
        concurrency: int = 1,
        skip_item_hashes: Iterable[str] | None = None,
    ) -> AsyncGenerator[SummaryChunk, None]:
        stream = super().summarize_stream(
            ctx=ctx,
            url=url,
            limit=limit,
            concurrency=concurrency,
            skip_item_hashes=skip_item_hashes,
            scraping_type="list-like",
            items_selector=".fie-impression-container",
            output_columns=POST_COLUMNS,
        )

        async for chunk in stream:
            yield chunk
