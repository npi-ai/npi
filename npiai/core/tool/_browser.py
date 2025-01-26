import base64
import io
from textwrap import dedent
from typing import Literal

from PIL import Image
from playwright.async_api import ElementHandle, TimeoutError

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from npiai.context import Context
from npiai.core.browser import PlaywrightContext
from npiai.utils import html_to_markdown, llm_tool_call

from ._function import FunctionTool, function


class BrowserTool(FunctionTool):
    use_screenshot: bool
    playwright: PlaywrightContext

    def __init__(
        self,
        playwright: PlaywrightContext = None,
        use_screenshot: bool = True,
        headless: bool = True,
    ):
        """
        Initialize a Browser App

        Args:
            playwright: Playwright context to use. A new playwright context is created if None.
            use_screenshot: Whether to send a screenshot of the current page to the vision model. This should be used with a navigator and a vision model.
            headless: Whether to run playwright in headless mode.
        """
        super().__init__()
        self.use_screenshot = use_screenshot
        self.playwright = playwright or PlaywrightContext(headless)

    async def load_page(
        self,
        ctx: Context,
        url: str,
        wait_for_selector: str = None,
        timeout: int | None = None,
        force_capcha_detection: bool = False,
    ):
        await self.playwright.page.goto(url)

        if wait_for_selector is not None:
            try:
                locator = self.playwright.page.locator(wait_for_selector)
                await locator.first.wait_for(state="attached", timeout=timeout)
            except TimeoutError:
                # if the selector is not found, check if a captcha is present
                force_capcha_detection = True
        # wait for the page to become stable
        elif timeout is not None:
            try:
                await self.playwright.page.wait_for_load_state(
                    "networkidle",
                    timeout=timeout,
                )
            except TimeoutError:
                pass

        # await self.playwright.page.wait_for_timeout(wait)

        if force_capcha_detection:
            await self.detect_captcha(ctx, return_to=url)

    @function
    async def get_text(self):
        """Get the text content (as markdown) of the current page"""
        html = await self.playwright.page.evaluate("() => document.body.innerHTML")
        return html_to_markdown(html)

    async def start(self):
        """Start the Browser App"""
        if not self._started:
            await super().start()
            await self.playwright.start()

    async def end(self):
        """Dispose the chrome tools"""
        await super().end()
        await self.playwright.stop()

    async def goto_blank(self):
        """
        Go to about:blank page
        This can be used as a cleanup function when a context finishes
        """
        await self.playwright.page.goto("about:blank")

    async def get_screenshot(
        self,
        full_page: bool = False,
        max_size: tuple[int, int] | None = None,
    ) -> str | None:
        """Get the screenshot of the current page"""
        if (
            not self.playwright
            or not self.playwright.ready
            or self.playwright.page.url == "about:blank"
        ):
            return None

        screenshot = await self.playwright.page.screenshot(
            caret="initial",
            full_page=full_page,
            # clip={"x": 0, "y": 0, "width": 1280, "height": 720 * 4},
        )

        if max_size:
            img = Image.open(io.BytesIO(screenshot))
            img.thumbnail(max_size)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            screenshot = buffer.getvalue()

        return "data:image/png;base64," + base64.b64encode(screenshot).decode()

    async def get_page_url(self):
        """Get the URL of the current page"""
        return self.playwright.page.url

    async def get_page_title(self):
        """Get the page title of the current page"""
        return await self.playwright.page.title()

    async def is_scrollable(self):
        """Check if the current page is scrollable"""
        return await self.playwright.page.evaluate("() => npi.isScrollable()")

    async def get_interactive_elements(self, screenshot: str, full_page: bool = False):
        """Get the interactive elements of the current page"""
        return await self.playwright.page.evaluate(
            """async ([screenshot, fullPage]) => {
                const { elementsAsJSON, addedIDs } = await npi.snapshot(screenshot, fullPage);
                return [elementsAsJSON, addedIDs];
            }""",
            [screenshot, full_page],
        )

    async def get_element_by_marker_id(self, elem_id: str):
        """Get the element by marker id"""
        handle = await self.playwright.page.evaluate_handle(
            "id => npi.getElement(id)",
            elem_id,
        )

        elem_handle = handle.as_element()

        if not elem_handle:
            raise Exception(f"Element not found (id: {elem_id})")

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
            "(elem) => npi.elementToJSON(elem)",
            elem,
        )

    async def init_observer(self):
        """Initialize a mutation observer on the current page"""
        await self.playwright.page.evaluate("() => npi.initObserver()")

    async def wait_for_stable(self):
        """Wait for the current page to be stable"""
        await self.playwright.page.evaluate("() => npi.stable()")

    async def add_bboxes(self, full_page: bool = False):
        """Add bounding boxes to the interactive elements on the current page"""
        await self.playwright.page.evaluate(
            "(fullPage) => npi.addBboxes(fullPage)",
            full_page,
        )

    async def clear_bboxes(self):
        """Clear the bounding boxes on the current page"""
        await self.playwright.page.evaluate("() => npi.clearBboxes()")

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
                "(elem) => npi.click(elem)",
                elem,
            )

        return f"Successfully clicked element"

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
                "([elem, value]) => npi.fill(elem, value)",
                [elem, value],
            )

        return f"Successfully filled value {value} into element"

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
                "([elem, value]) => npi.select(elem, value)",
                [elem, value],
            )

        return f"Successfully selected value {value} for element"

    async def enter(self, elem: ElementHandle):
        """
        Press Enter on an input field. This action usually submits a form.

        Args:
            elem: Element Handle of the target element
        """

        try:
            await elem.press("Enter")
        except TimeoutError:
            await self.playwright.page.evaluate(
                "(elem) => npi.enter(elem)",
                elem,
            )

        return f"Successfully pressed Enter on element"

    async def scroll(self):
        """
        Scroll the page down to reveal more contents
        """

        await self.playwright.page.evaluate("() => npi.scrollPageDown()")
        await self.playwright.page.wait_for_timeout(300)

        return f"Successfully scrolled down to reveal more contents"

    async def back_to_top(self):
        """
        Scroll the page back to the top to start over
        """

        await self.playwright.page.evaluate("() => window.scrollTo(0, 0)")
        await self.playwright.page.wait_for_timeout(300)

        return f"Successfully scrolled to top"

    async def detect_captcha(self, ctx: Context, return_to: str | None = None):
        url = await self.get_page_url()
        screenshot = await self.get_screenshot(full_page=True, max_size=(1280, 720))

        async def handle_captcha(captcha_type: Literal["none", "captcha", "login"]):
            """
            Handle the captcha detection result

            Args:
                captcha_type: "none" if no captcha is detected, "captcha" if a captcha is detected, "login" if a login form is detected
            """
            match captcha_type:
                case "captcha":
                    await ctx.hitl.web_interaction(
                        tool_name=self.name,
                        message="Would you please help me solve the captcha?",
                        url=url,
                        action="captcha",
                        playwright=self.playwright,
                    )
                case "login":
                    await ctx.hitl.web_interaction(
                        tool_name=self.name,
                        message="Would you please help me login to the website?",
                        url=url,
                        action="login",
                        playwright=self.playwright,
                    )

            if (
                captcha_type != "none"
                and return_to
                and self.playwright.page.url != return_to
            ):
                # TODO: do we need to check captcha again after returning to the original page?
                await self.load_page(ctx, return_to)

            return captcha_type

        res = await llm_tool_call(
            llm=ctx.llm,
            tool=handle_captcha,
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=dedent(
                        """
                        You are given a screenshot of a webpage. Determine if a captcha or login form is present in the screenshot. If a captcha is present, call the tool with the argument "captcha". If a login form is present, call the tool with the argument "login". If neither is present, call the tool with the argument "none".
                        """
                    ),
                ),
                ChatCompletionUserMessageParam(
                    role="user",
                    content=[
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": screenshot,
                            },
                        }
                    ],
                ),
            ],
        )

        return await handle_captcha(**res.model_dump())
