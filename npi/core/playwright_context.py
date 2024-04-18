import pathlib
import subprocess

from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page, FileChooser


# TODO: publish the js package to npm
def _prepare_browser_utils():
    # path to the js bundle
    js_dir = pathlib.Path(__file__).parent / '../../browser-utils'

    subprocess.call('pnpm install && pnpm build', shell=True, cwd=js_dir)

    return js_dir / 'dist/index.global.js'


class PlaywrightContext:
    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page
    headless: bool

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

    async def start(self):
        """Start the Playwright browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)

        self.context = await self.browser.new_context(
            locale='en-US',
            **self.playwright.devices['Desktop Chrome'],
        )
        self.context.set_default_timeout(3000)
        await self.context.add_init_script(path=_prepare_browser_utils())
        await self.context.add_init_script(script="""window.npi = new window.BrowserUtils()""")

        self.page = await self.context.new_page()
        self.page.on('filechooser', self.on_filechooser)
        self.page.on('popup', self.on_popup)

    async def on_filechooser(self, chooser: FileChooser):
        """
        Callback function invoked when an input:file is clicked

        Args:
            chooser: FileChooser instance
        """
        await chooser.set_files('')

    async def on_popup(self, popup: Page):
        """
        Callback function invoked when a tab is opened

        Args:
            popup: Page instance
        """
        self.page = popup

    async def stop(self):
        """
        Dispose the browser app
        """
        await self.playwright.stop()
