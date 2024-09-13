from abc import ABC, abstractmethod
from typing import List

from npiai.context import Context
from npiai.core.base import BaseTool


class BaseTaskTuner(ABC):
    @abstractmethod
    async def tune(
        self,
        ctx: Context,
        instruction: str,
        tool: BaseTool,
        related_tasks: List[str] | None = None,
    ) -> str: ...
