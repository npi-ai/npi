from abc import ABC, abstractmethod
from typing import TypeVar, Type

_T = TypeVar("_T")


class BaseMemory(ABC):
    @abstractmethod
    async def save(self, info: str): ...

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        return_type: Type[_T] = str,
        constraints: str = None,
        _is_retry: bool = False,
    ) -> _T: ...
