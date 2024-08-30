from dataclasses import dataclass
from typing import List, TYPE_CHECKING, Optional

from .execution_step import ExecutionStep

if TYPE_CHECKING:
    from npiai.core import BaseTool


@dataclass(frozen=True)
class Plan:
    steps: List[ExecutionStep]
    tool: "BaseTool"
