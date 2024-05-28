from typing import Callable, Optional, Awaitable, List, Dict, Any
from dataclasses import dataclass, asdict
from .shot import Shot

ToolFunction = Callable[..., Awaitable[str]]


@dataclass(frozen=True)
class FunctionRegistration:
    fn: ToolFunction
    description: str
    name: str
    code: str
    schema: Optional[Dict[str, Any]] = None
    few_shots: Optional[List[Shot]] = None

    def get_meta(self):
        return {
            'description': self.description,
            'name': self.name,
            'code': self.code,
            'parameters': self.schema,
            'fewShots': [asdict(ex) for ex in self.few_shots] if self.few_shots else None,
        }
