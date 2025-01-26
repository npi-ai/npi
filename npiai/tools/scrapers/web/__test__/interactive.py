import asyncio
from typing import Literal

from npiai.utils.test_utils import DebugContext

# from npiai import Context
from utils import auto_scrape

from npiai import HITL


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
    ) -> str:
        print(f"[HITL] web_interaction: {message=}, {url=}, {action=}")
        return "web_interaction"


async def main():
    url = input("Enter the URL: ")
    ctx = DebugContext()
    ctx.use_hitl(TestHITL())
    # url = "https://www.bardeen.ai/playbooks"

    await auto_scrape(
        ctx=ctx,
        url=url,
    )


if __name__ == "__main__":
    asyncio.run(main())
