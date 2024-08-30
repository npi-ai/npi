from abc import ABC, abstractmethod
from typing import List

from npiai.context import Context
from npiai.types import FunctionRegistration, ExecutionStep


class BasePlanner(ABC):
    @abstractmethod
    async def generate_plan(
        self,
        ctx: Context,
        instruction: str,
        functions: List[FunctionRegistration],
    ) -> List[ExecutionStep]: ...
