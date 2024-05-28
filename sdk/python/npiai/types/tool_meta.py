from dataclasses import dataclass
from typing import Optional, Type, List

from npi.v1.types import Parameters, Shot


@dataclass(frozen=True)
class ToolMeta:
    name: str
    description: str
    code: str
    Params: Optional[Type[Parameters]] = None
    few_shots: Optional[List[Shot]] = None
