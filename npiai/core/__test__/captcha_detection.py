import asyncio
from typing import Literal

from npiai import BrowserTool, HITL
from npiai.core import PlaywrightContext
from npiai.utils.test_utils import DebugContext


class TestHITL(HITL):
    async def confirm(
        self,
        tool_name: str,
        message: str,
        default=False,
    ) -> bool:
        print(f"[HITL] confirm: {message=}, {default=}")
        return True

    async def input(
        self,
        tool_name: str,
        message: str,
        default="",
    ) -> str:
        print(f"[HITL] input: {message=}, {default=}")
        return "input"

    async def select(
        self,
        tool_name: str,
        message: str,
        choices: list[str],
        default="",
    ) -> str:
        print(f"[HITL] select: {message=}, {choices=}, {default=}")
        return "select"

    async def web_interaction(
        self,
        tool_name: str,
        message: str,
        url: str,
        action: Literal["captcha", "login"],
        playwright: PlaywrightContext,
    ) -> str:
        print(f"[HITL] web_interaction: {message=}, {url=}, {action=}")
        await playwright.restore_state(await playwright.get_state())
        return "web_interaction"


urls = [
    "https://www.google.com/recaptcha/api2/demo",
    "https://nopecha.com/captcha/turnstile",
    "https://github.com/login",
    "https://google.com",
    "https://x.com/elonmusk",
]


async def main():
    ctx = DebugContext()
    ctx.use_hitl(TestHITL())

    async with BrowserTool(headless=False) as tool:
        for url in urls:
            await tool.load_page(ctx, url)
            captcha_type = await tool.detect_captcha(ctx, return_to=url)
            print(f"{url}: {captcha_type}")


if __name__ == "__main__":
    asyncio.run(main())
