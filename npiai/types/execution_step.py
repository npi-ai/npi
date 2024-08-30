from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING, Optional
from uuid import uuid4

from .function_registration import FunctionRegistration

if TYPE_CHECKING:
    from .plan import Plan


@dataclass(frozen=True)
class ExecutionStep:
    task: str
    id: str = field(default_factory=lambda: str(uuid4()))
    fn_candidates: List[FunctionRegistration] = field(default_factory=list)
    sub_plan: Optional["Plan"] = None

    def to_json_object(self) -> dict:
        return {
            "id": self.id,
            "task": self.task,
            "fn_candidates": [fn.name for fn in self.fn_candidates],
            "sub_plan": (self.sub_plan.to_json_object() if self.sub_plan else None),
        }
