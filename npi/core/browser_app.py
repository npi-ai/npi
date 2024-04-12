import pathlib
import subprocess

from openai import Client
from openai.types.chat import ChatCompletionToolChoiceOptionParam
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page, FileChooser

from npi.core.app import App


# TODO: publish the js package to npm
def _prepare_browser_utils():
    # path to the js bundle
    js_dir = pathlib.Path(__file__).parent / '../../browser-utils'

    subprocess.call('pnpm install && pnpm build', shell=True, cwd=js_dir)

    return js_dir / 'dist/index.global.js'


class BrowserApp(App):
    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page

    def __init__(
        self,
        name: str,
        description: str,
        llm: Client = None,
        system_role: str = None,
        model: str = "gpt-4-vision-preview",
        tool_choice: ChatCompletionToolChoiceOptionParam = "auto",
        headless: bool = True,
    ):
        super().__init__(name, description, llm, system_role, model, tool_choice)

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)

        self.context = self.browser.new_context(locale='en-US')
        self.context.set_default_timeout(3000)
        self.context.add_init_script(path=_prepare_browser_utils())

        self.page = self.context.new_page()
        self.page.on('filechooser', self.on_filechooser)
        self.page.on('popup', self.on_popup)

    def on_filechooser(self, chooser: FileChooser):
        chooser.set_files('')

    def on_popup(self, popup: Page):
        self.page = popup

    def dispose(self):
        self.playwright.stop()
