from typing import List, Literal

import questionary
from questionary import Style

from npiai.core import HITL, PlaywrightContext

_PROMPT_STYLE = Style(
    [
        ("question", "magenta"),
    ]
)


class ConsoleHandler(HITL):
    async def confirm(
        self,
        tool_name: str,
        message: str,
        default=False,
    ) -> bool:
        return await questionary.confirm(
            message=f"[{tool_name}]: Please confirm: {message}",
            default=default,
            style=_PROMPT_STYLE,
        ).ask_async()

    async def input(
        self,
        tool_name: str,
        message: str,
        default="",
    ) -> str:
        return await questionary.text(
            message=f"[{tool_name}]: {message}:",
            default=default,
            style=_PROMPT_STYLE,
        ).ask_async()

    async def select(
        self,
        tool_name: str,
        message: str,
        choices: List[str],
        default: str = None,
    ) -> str:
        return await questionary.select(
            message=f"[{tool_name}]: {message}",
            choices=choices,
            default=default,
            style=_PROMPT_STYLE,
        ).ask_async()

    async def web_interaction(
        self,
        tool_name: str,
        message: str,
        url: str,
        action: Literal["captcha", "login", "other"],
        playwright: PlaywrightContext,
    ) -> str:
        return await questionary.text(
            message=f"[{tool_name}]: {message}",
            default="I have completed the action",
            style=_PROMPT_STYLE,
        ).ask_async()
