from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FromVectorDB:
    query: str
    constraints: str | None = None
    # generated attributes
    name: str = None
    return_type: Any = None
