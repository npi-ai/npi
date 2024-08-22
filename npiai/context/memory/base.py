from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from npiai.context import Context


class BaseMemory(ABC):
    _ctx: "Context"

    def __init__(self, context: "Context"):
        self._ctx = context

    # @abstractmethod
    # async def save(self, info: str): ...
    #
    # @abstractmethod
    # async def ask(
    #     self,
    #     ctx: "Context",
    #     query: str,
    #     return_type: Type[_T] = str,
    #     constraints: str = None,
    #     _is_retry: bool = False,
    # ) -> _T: ...
