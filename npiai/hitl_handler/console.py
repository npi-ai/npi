from typing import List

import questionary

from termcolor import colored
from npiai.core import HITL
from npiai.context import Context


class ConsoleHandler(HITL):
    async def confirm(
        self,
        ctx: Context,
        tool_name: str,
        message: str,
        default=False,
    ) -> bool:
        return await questionary.confirm(
            colored(
                f"[{tool_name}]: Please confirm: {message}",
                color="magenta",
                attrs=["bold"],
            ),
            default=default,
        ).ask_async()

    async def input(
        self,
        ctx: Context,
        tool_name: str,
        message: str,
        default="",
    ) -> str:
        print(colored(f"[{tool_name}]: {message}", color="magenta", attrs=["bold"]))
        return await questionary.text(
            "Type your response:", default=default
        ).ask_async()

    async def select(
        self,
        ctx: Context,
        tool_name: str,
        message: str,
        choices: List[str],
        default: str = None,
    ) -> str:
        return await questionary.select(
            message=colored(
                f"[{tool_name}]: {message}",
                color="magenta",
                attrs=["bold"],
            ),
            choices=choices,
            default=default,
        ).ask_async()
