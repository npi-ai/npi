from abc import ABC, abstractmethod
from typing import List

from npiai.context import Context


class HITL(ABC):
    ctx: Context

    def bind_context(self, ctx: Context):
        self.ctx = ctx

    @abstractmethod
    async def confirm(
        self,
        tool_name: str,
        message: str,
        default=False,
    ) -> bool: ...

    @abstractmethod
    async def input(
        self,
        tool_name: str,
        message: str,
        default="",
    ) -> str: ...

    @abstractmethod
    async def select(
        self,
        tool_name: str,
        message: str,
        choices: List[str],
        default="",
    ): ...
