from abc import ABC


class BaseMemory(ABC):
    _context_id: str

    def __init__(self, context_id: str):
        self._context_id = context_id

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
