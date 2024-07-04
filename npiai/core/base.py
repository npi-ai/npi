import os
from abc import ABC, abstractmethod
from typing import List

import yaml
from litellm.types.completion import ChatCompletionToolMessageParam
from litellm.types.utils import ChatCompletionMessageToolCall

from npiai.types import FunctionRegistration
from npiai.utils import logger
from npiai.core.hitl import HITL
from npiai.context import Context


class BaseTool(ABC):

    def __init__(self, name: str, description: str, provider: str = 'npiai'):
        self.name = name
        self.description = description
        self.provider = provider
        self._hitl: HITL | None = None

    @property
    def hitl(self) -> HITL:
        if self._hitl is None:
            raise AttributeError('HITL handler has not been set')

        return self._hitl

    @abstractmethod
    def unpack_functions(self) -> List[FunctionRegistration]:
        """Export the functions registered in the tools"""
        ...

    @abstractmethod
    def server(self):
        """Start the tools"""
        ...

    @abstractmethod
    async def start(self):
        """Start the tools"""
        ...

    @abstractmethod
    async def end(self):
        """Stop and dispose the tools"""
        ...

    def use_hitl(self, hitl: HITL):
        self._hitl = hitl

    def export(self, filename: str | None = None):
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
                'functions': [t.get_meta() for t in self.unpack_functions()],
            }
        }

        if filename is not None:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                yaml.dump(data, f)
                logger.info(f'Exported schema to: {filename}')
        else:
            return data

    async def get_screenshot(self) -> str | None:
        return None

    # context manager
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.end()


class BaseFunctionTool(BaseTool, ABC):
    @abstractmethod
    async def call(
            self,
            tool_calls: List[ChatCompletionMessageToolCall],
            ctx: Context = None,
    ) -> List[ChatCompletionToolMessageParam]:
        ...


class BaseAgentTool(BaseTool, ABC):
    @abstractmethod
    async def chat(
            self,
            message: str,
            thread: Context = None,
    ) -> str:
        ...
