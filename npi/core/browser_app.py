import base64
from openai import Client
from openai.types.chat import ChatCompletionToolChoiceOptionParam
from playwright.async_api import ElementHandle
from markdownify import markdownify

from npi.core.app import App, npi_tool
from npiai_proto import api_pb2
from .playwright_context import PlaywrightContext

from npi.core.thread import Thread


class BrowserApp(App):
    playwright: PlaywrightContext
    use_screenshot: bool

    def __init__(
        self,
        name: str,
        description: str,
        llm: Client = None,
        system_role: str = None,
        model: str = "gpt-4-vision-preview",
        tool_choice: ChatCompletionToolChoiceOptionParam = "auto",
        playwright: PlaywrightContext = None,
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
            use_screenshot: Whether to send a screenshot of the current page to the vision model. This should be used with a navigator and a vision model.
            headless: Whether to run playwright in headless mode
        """
        super().__init__(name, description, llm, system_role, model, tool_choice)
        self.use_screenshot = use_screenshot
        self.playwright = playwright or PlaywrightContext(headless)

    @npi_tool
    async def get_text(self):
        """Get the text content (as markdown) of the current page"""
        html = await self.playwright.page.evaluate('() => document.body.innerHTML')
        return markdownify(html)

    async def start(self, thread: Thread = None):
        """Start the Browser App"""
        if not self._started:
            await super().start(thread)
            await self.playwright.start()

    async def dispose(self):
        """
        Dispose the browser app
        """
        await super().dispose()
        await self.playwright.stop()

    async def chat(
        self,
        message: str,
        thread: Thread = None,
    ) -> str:
        if not self._started:
            await self.start()

        if not self.use_screenshot:
            return await super().chat(message, thread)

        if thread is None:
            thread = Thread('', api_pb2.APP_UNKNOWN)

        screenshot = await self.get_screenshot()

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

    async def get_screenshot(self):
        """Get the screenshot of the current page"""
        if not self.playwright or not self.playwright.ready or self.playwright.page.url == 'about:blank':
            return None
        screenshot = await self.playwright.page.screenshot(caret='initial')
        return 'data:image/png;base64,' + base64.b64encode(screenshot).decode()

    async def get_page_url(self):
        """Get the URL of the current page"""
        return self.playwright.page.url

    async def get_page_title(self):
        """Get the page title of the current page"""
        return await self.playwright.page.title()

    async def is_scrollable(self):
        """Check if the current page is scrollable"""
        return await self.playwright.page.evaluate('() => npi.isScrollable()')

    async def get_interactive_elements(self, screenshot: str):
        """Get the interactive elements of the current page"""
        return await self.playwright.page.evaluate(
            """async (screenshot) => {
                const { elementsAsJSON, addedIDs } = await npi.snapshot(screenshot);
                return [elementsAsJSON, addedIDs];
            }""",
            screenshot,
        )

    async def get_element_by_marker_id(self, elem_id: str):
        """Get the element by marker id"""
        handle = await self.playwright.page.evaluate_handle(
            'id => npi.getElement(id)',
            elem_id,
        )

        elem_handle = handle.as_element()

        if not elem_handle:
            raise Exception(f'Element not found (id: {elem_id})')

        return elem_handle

    async def element_to_json(self, elem: ElementHandle):
        """
        Convert the element into JSON

        Args:
            elem: Playwright element handle

        Returns:
            JSON representation of the element
        """
        return await self.playwright.page.evaluate(
            '(elem) => npi.elementToJSON(elem)',
            elem,
        )

    async def init_observer(self):
        """Initialize a mutation observer on the current page"""
        await self.playwright.page.evaluate('() => npi.initObserver()')

    async def wait_for_stable(self):
        """Wait for the current page to be stable"""
        await self.playwright.page.evaluate('() => npi.stable()')

    async def add_bboxes(self):
        """Add bounding boxes to the interactive elements on the current page"""
        await self.playwright.page.evaluate('() => npi.addBboxes()')

    async def clear_bboxes(self):
        """Clear the bounding boxes on the current page"""
        await self.playwright.page.evaluate('() => npi.clearBboxes()')

    async def click(self, elem: ElementHandle):
        """
        Click an element on the page

        Args:
            elem: Element Handle of the target element
        """

        try:
            await elem.click()
        except TimeoutError:
            await self.playwright.page.evaluate(
                '(elem) => npi.click(elem)',
                elem,
            )

        return f'Successfully clicked element'

    async def fill(self, elem: ElementHandle, value: str):
        """
        Fill in an input field on the page

        Args:
            elem: Element Handle of the target element
            value: value to fill
        """

        try:
            await elem.fill(value)
        except TimeoutError:
            await self.playwright.page.evaluate(
                '([elem, value]) => npi.fill(elem, value)',
                [elem, value],
            )

        return f'Successfully filled value {value} into element'

    async def select(self, elem: ElementHandle, value: str):
        """
        Select an option for a <select> element

        Args:
            elem: Element Handle of the target element
            value: value to select
        """

        try:
            await elem.select_option(value)
        except TimeoutError:
            await self.playwright.page.evaluate(
                '([elem, value]) => npi.select(elem, value)',
                [elem, value],
            )

        return f'Successfully selected value {value} for element'

    async def enter(self, elem: ElementHandle):
        """
        Press Enter on an input field. This action usually submits a form.

        Args:
            elem: Element Handle of the target element
        """

        try:
            await elem.press('Enter')
        except TimeoutError:
            await self.playwright.page.evaluate(
                '(elem) => npi.enter(elem)',
                elem,
            )

        return f'Successfully pressed Enter on element'

    async def scroll(self):
        """
        Scroll the page down to reveal more contents
        """

        await self.playwright.page.evaluate('() => npi.scrollPageDown()')
        await self.playwright.page.wait_for_timeout(300)

        return f'Successfully scrolled down to reveal more contents'

    async def back_to_top(self):
        """
        Scroll the page back to the top to start over
        """

        await self.playwright.page.evaluate('() => window.scrollTo(0, 0)')
        await self.playwright.page.wait_for_timeout(300)

        return f'Successfully scrolled to top'
