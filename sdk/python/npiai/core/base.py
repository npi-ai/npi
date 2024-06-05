import os
from abc import ABC, abstractmethod
from typing import List

import yaml
from litellm.types.completion import ChatCompletionToolMessageParam
from litellm.utils import ChatCompletionMessageToolCall

from npiai.types import FunctionRegistration
from npiai.utils import logger


class NPiBase(ABC):
    name: str
    description: str
    provider: str

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

    def export(self, filename: str):
        """
        Find the wrapped tool functions and export them as yaml
        """
        data = {
            'kind': 'Function',
            'metadata': {
                'name': self.name,
                'description': self.description,
                'provider': self.provider,
            },
            'spec': {
                'runtime': {
                    'language': 'python',
                    'version': '3.11',
                },
                'dependencies': [{
                    'name': 'npiai',
                    'version': '0.1.0',
                }],
                'functions': [t.get_meta() for t in self.list_functions()],
            }
        }

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w') as f:
            yaml.dump(data, f)
            logger.info(f'Exported schema to: {filename}')

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
