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
    StorageState,
    Dialog,
    Download,
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
    headless: bool
    ready: bool
    playwright: Playwright | None
    browser: Browser | None
    context: BrowserContext | None
    page: Page | None
    channel: str | None
    storage_state: str | pathlib.Path | StorageState | None

    def __init__(
        self,
        headless: bool = True,
        channel: str | None = None,
        storage_state: str | pathlib.Path | StorageState | None = None,
    ):
        """
        Initialize a Playwright context

        Args:
            headless: Whether to run playwright in headless mode
            channel: The browser channel to use, see: https://playwright.dev/python/docs/browsers#google-chrome--microsoft-edge
            storage_state: Previously saved state to use for the browser context
        """
        self.headless = headless
        self.ready = False
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.channel = channel
        self.storage_state = storage_state

    async def start(self):
        """Start the Playwright chrome"""
        if self.ready:
            return

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            channel=self.channel,
            args=["--disable-blink-features=AutomationControlled"],
            # args=["--disable-gpu", "--single-process"],
        )

        self.context = await self.browser.new_context(
            locale="en-US",
            bypass_csp=True,
            storage_state=self.storage_state,
            **self.playwright.devices["Desktop Chrome"],
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
        self.attach_events(self.page)

        self.ready = True

    def attach_events(self, page: Page):
        page.on("dialog", self.on_dialog)
        page.on("download", self.on_download)
        page.on("filechooser", self.on_filechooser)
        page.on("popup", self.on_popup)
        page.on("close", self.on_close)

    async def on_dialog(self, dialog: Dialog):
        """
        Callback function invoked when a dialog is opened

        Args:
            dialog: Dialog instance
        """
        await dialog.dismiss()

    async def on_download(self, download: Download):
        """
        Callback function invoked when a download is started

        Args:
            download: Download instance
        """
        await download.cancel()

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
        await popup.set_viewport_size(self.page.viewport_size)
        self.page = popup
        self.attach_events(popup)

    async def on_close(self, _):
        """
        Callback function invoked when the page is closed
        """
        if self.context.pages:
            self.page = self.context.pages[-1]
            self.attach_events(self.page)

    async def stop(self):
        """
        Dispose the chrome tools
        """
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()
