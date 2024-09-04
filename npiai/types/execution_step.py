from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING, Optional
from uuid import uuid4

from .function_registration import FunctionRegistration

if TYPE_CHECKING:
    from .plan import Plan


@dataclass(frozen=True)
class ExecutionStep:
    task: str
    thought: str
    id: str = field(default_factory=lambda: str(uuid4()))
    potential_tools: List[FunctionRegistration] = field(default_factory=list)
    sub_plan: Optional["Plan"] = None

    def to_json_object(self) -> dict:
        return {
            "id": self.id,
            "task": self.task,
            "thought": self.thought,
            "potential_tools": [fn.name for fn in self.potential_tools],
            "sub_plan": (self.sub_plan.to_json_object() if self.sub_plan else None),
        }
