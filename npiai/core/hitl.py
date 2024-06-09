from abc import ABC, abstractmethod


class HITL(ABC):
    @abstractmethod
    async def confirm(self, app_name: str, message: str) -> bool:
        ...

    @abstractmethod
    async def input(self, app_name: str, message: str) -> str:
        ...
