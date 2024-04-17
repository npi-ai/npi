import pathlib
import subprocess

from openai import Client
from openai.types.chat import ChatCompletionToolChoiceOptionParam
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page, FileChooser
from typing import Union

from npi.core.app import App
from npi.core.navigator import Navigator
from npi.core.thread import Thread
from proto.python.api import api_pb2


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
    headless: bool
    use_screenshot: bool
    navigator: Union[Navigator, None] = None
    started: bool = False

    def __init__(
        self,
        name: str,
        description: str,
        llm: Client = None,
        system_role: str = None,
        model: str = "gpt-4-vision-preview",
        tool_choice: ChatCompletionToolChoiceOptionParam = "auto",
        use_navigator: Union[bool, Navigator] = True,
        use_screenshot: bool = True,
        headless: bool = True,
    ):
        """
        Initialize a Browser App

        Args:
            name: Name of the browser app
            description: A brief description of the browser app. This will be used if the app is called as a tool
            llm: LLM instance
            system_role: System prompt of the browser app
            model: LLM model to use
            tool_choice: LLM tool choice
            use_navigator: Whether to use navigator. If True, the default navigator will be used. If a navigator instance is provided, it will replace the default navigator
            use_screenshot: Whether to send a screenshot of the current page to the vision model. This should be used with a navigator and a vision model.
            headless: Whether to run playwright in headless mode
        """
        super().__init__(name, description, llm, system_role, model, tool_choice)
        self.headless = headless
        self.use_screenshot = use_screenshot

        if use_navigator:
            self.navigator = use_navigator if isinstance(use_navigator, Navigator) else Navigator(self)
            self.register(self.navigator)

    async def start(self):
        """Start the Browser App"""
        if self.started:
            return

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

        self.started = True

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

    async def dispose(self):
        """
        Dispose the browser app
        """
        await self.playwright.stop()

    async def chat(
        self,
        message: str,
        thread: Thread = None,
    ) -> str:
        if not self.started:
            await self.start()

        if not self.use_screenshot or not self.navigator:
            return await super().chat(message, thread)

        if thread is None:
            thread = Thread('', api_pb2.APP_UNKNOWN)

        screenshot = await self.navigator.get_screenshot()

        msg = thread.fork(message)

        if self.system_role:
            msg.append(
                {
                    'role': 'system',
                    'content': self.system_role,
                }
            )

        msg.append(
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': message,
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': screenshot,
                        },
                    },
                ]
            }
        )

        return await self._call_llm(thread, msg)
