from abc import ABC, abstractmethod

from npiai.context import Context


class HITL(ABC):
    @abstractmethod
    async def confirm(
        self,
        ctx: Context,
        tool_name: str,
        message: str,
        default=False,
    ) -> bool: ...

    @abstractmethod
    async def input(
        self,
        ctx: Context,
        tool_name: str,
        message: str,
        default="",
    ) -> str: ...
