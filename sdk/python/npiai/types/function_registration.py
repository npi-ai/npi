from typing import Callable, Type, Optional, Awaitable, List, Dict, Any
from dataclasses import dataclass, asdict
from .parameters import Parameters
from .example import Example

ToolFunction = Callable[[Parameters], str | Awaitable[str]]


@dataclass(frozen=True)
class FunctionRegistration:
    fn: ToolFunction
    description: str
    name: str
    code: str
    schema: Optional[Dict[str, Any]] = None
    examples: Optional[List[Example]] = None

    def get_meta(self):
        return {
            'description': self.description,
            'name': self.name,
            'code': self.code,
            'parameters': self.schema,
            'examples': [asdict(ex) for ex in self.examples] if self.examples else None,
        }
