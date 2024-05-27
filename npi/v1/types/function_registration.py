from typing import Callable, Type, Optional, Awaitable, List
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
    Params: Optional[Type[Parameters]] = None
    few_shots: Optional[List[Shot]] = None

    def get_meta(self):
        return {
            'description': self.description,
            'name': self.name,
            'code': self.code,
            'parameters': self.Params.get_meta_schema() if self.Params else None,
            'fewShots': [asdict(s) for s in self.few_shots] if self.few_shots else None,
        }
