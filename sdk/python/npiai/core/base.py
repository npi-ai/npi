from abc import ABC, abstractmethod
from typing import List

from litellm.types.completion import ChatCompletionToolMessageParam
from litellm.utils import ChatCompletionMessageToolCall

from npiai.types import FunctionRegistration


class NPiBase(ABC):
    name: str
    description: str

    @abstractmethod
    def list_functions(self) -> List[FunctionRegistration]:
        """Export the functions registered in the app"""
        ...

    @abstractmethod
    async def start(self):
        """Start the app"""
        ...

    @abstractmethod
    async def end(self):
        """Stop and dispose the app"""
        ...

    # context manager
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.end()


class BaseApp(NPiBase, ABC):
    @abstractmethod
    async def call(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
    ) -> List[ChatCompletionToolMessageParam]:
        ...


class BaseAgent(NPiBase, ABC):
    @abstractmethod
    async def chat(self, message: str) -> str:
        ...
