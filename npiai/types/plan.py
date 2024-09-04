from dataclasses import dataclass
from typing import List, TYPE_CHECKING

from .execution_step import ExecutionStep

if TYPE_CHECKING:
    from npiai.core import BaseTool


@dataclass(frozen=True)
class Plan:
    goal: str
    steps: List[ExecutionStep]
    toolset: "BaseTool"

    def to_json_object(self) -> dict:
        return {
            "goal": self.goal,
            "steps": [step.to_json_object() for step in self.steps],
            "toolset": self.toolset.name,
        }
