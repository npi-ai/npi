from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Type
from pydantic import BaseModel

from npiai.types.shot import Shot


@dataclass(frozen=True)
class ToolMeta:
    name: str
    description: str
    schema: Dict[str, Any] = None
    model: Optional[Type[BaseModel]] = None
    few_shots: Optional[List[Shot]] = None
