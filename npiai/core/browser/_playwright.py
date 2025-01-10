import os
import pathlib
import tempfile
from textwrap import dedent
from urllib.request import urlretrieve

from playwright.async_api import (
    async_playwright,
    Playwright,
    Browser,
    BrowserContext,
    Page,
    FileChooser,
)

__BROWSER_UTILS_VERSION__ = "0.0.15"


def _prepare_browser_utils():
    # path to the js bundle
    cache_dir = pathlib.Path(tempfile.gettempdir()) / ".npi"
    js_path = cache_dir / f"chrome-utils@{__BROWSER_UTILS_VERSION__}.js"

    if js_path.exists():
        return js_path

    os.makedirs(cache_dir, exist_ok=True)

    urlretrieve(
        f"https://unpkg.com/@npi-ai/browser-utils@{__BROWSER_UTILS_VERSION__}/dist/index.global.js",
        js_path,
    )

    return js_path


class PlaywrightContext:
    def __init__(
        self,
        headless: bool = True,
    ):
        """
        Initialize a Playwright context

        Args:
            headless: Whether to run playwright in headless mode
        """
        self.headless = headless
        self.ready = False
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def start(self):
        """Start the Playwright chrome"""
        if self.ready:
            return

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            # args=["--disable-gpu", "--single-process"],
        )

        self.context = await self.browser.new_context(
            locale="en-US",
            bypass_csp=True,
            **self.playwright.devices["Desktop Edge"],
        )
        # self.context.set_default_timeout(3000)
        await self.context.add_init_script(path=_prepare_browser_utils())
        await self.context.add_init_script(
            script=dedent(
                """
                window.npi = new window.BrowserUtils();
                window['ga-disable-GA_MEASUREMENT_ID'] = true;
                """
            )
        )

        def block_route(route):
            return route.fulfill(status=204, body="")

        # block Google Analytics
        await self.context.route(
            "https://www.googletagmanager.com/gtag/**/*",
            block_route,
        )

        # block cloudflare challenges
        await self.context.route(
            "https://challenges.cloudflare.com/**/*",
            block_route,
        )

        self.page = await self.context.new_page()
        self.page.on("filechooser", self.on_filechooser)
        self.page.on("popup", self.on_popup)

        self.ready = True

    async def on_filechooser(self, chooser: FileChooser):
        """
        Callback function invoked when an input:file is clicked

        Args:
            chooser: FileChooser instance
        """
        await chooser.set_files("")

    async def on_popup(self, popup: Page):
        """
        Callback function invoked when a tab is opened

        Args:
            popup: Page instance
        """
        print(f"popup {popup}")
        self.page = popup

    async def stop(self):
        """
        Dispose the chrome tools
        """
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()
