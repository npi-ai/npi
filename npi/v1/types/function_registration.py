from typing import Callable, Type, Optional, Awaitable, List, Dict, Any
from dataclasses import dataclass, asdict
from .parameters import Parameters
from .shot import Shot

ToolFunction = Callable[[Parameters], str | Awaitable[str]]


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
            'fewShots': [asdict(s) for s in self.few_shots] if self.few_shots else None,
        }
