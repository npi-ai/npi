import datetime
from abc import ABC, ABCMeta, abstractmethod
from typing import List, Dict, Any

from litellm.types.completion import ChatCompletionToolMessageParam
from litellm.types.utils import ChatCompletionMessageToolCall
from openai.types.chat import ChatCompletionToolParam

from npiai.types import FunctionRegistration
from npiai.context import Context
from npiai.core.hitl import HITL


#
# class CombinedMeta(ABCMeta, type):
#     def __init__(cls, name, bases, attrs):
#         super().__init__(name, bases, attrs)
#
#         # Skip the check for the base class itself
#         if not any(isinstance(base, CombinedMeta) for base in bases):
#             return
#
#         # Get the required variables from the parent classes
#         parent_vars = {k for base in bases for k, v in base.__dict__.items() if
#                        not k.startswith('__') and not callable(v)}
#         subclass_vars = set(attrs.keys())
#
#         # Find the missing overrides
#         missing_overrides = parent_vars - subclass_vars
#         if missing_overrides:
#             raise TypeError(f"Subclasses must override variables: {', '.join(missing_overrides)}")


class BaseTool(ABC):  #, metaclass=CombinedMeta

    @classmethod
    def from_context(cls, ctx: Context) -> 'BaseTool':
        # bind the tool to the Context
        raise NotImplementedError("subclasses must implement this method for npi cloud hosting")

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        pass

    def __init__(self, name: str = "", description: str = "", provider: str = 'npiai',
                 fn_map: Dict[str, FunctionRegistration] | None = None):
        self.name = name
        self.description = description
        self.provider = provider
        self._fn_map = fn_map or {}
        self._hitl: HITL | None = None
        # self._context = _context

    @property
    def hitl(self) -> HITL:
        if self._hitl is None:
            raise AttributeError('HITL handler has not been set')

        return self._hitl

    @property
    def tools(self) -> List[ChatCompletionToolParam]:
        fns = self.unpack_functions()
        result = []
        for fn in fns:
            result.append(fn.get_tool_param())
        return result

    @abstractmethod
    def unpack_functions(self) -> List[FunctionRegistration]:
        """Export the functions registered in the tools"""
        ...

    @abstractmethod
    async def start(self):
        """Start the tools"""
        ...

    @abstractmethod
    async def end(self):
        """Stop and dispose the tools"""
        ...

    async def exec(self, ctx: Context, fn_name: str, args: Dict[str, Any] = None):
        time1 = datetime.datetime.now()

        if fn_name not in self._fn_map:
            raise RuntimeError(
                f'[{self.name}]: function `{fn_name}` not found. Available functions: {self._fn_map.keys()}'
            )

        fn = self._fn_map[fn_name]

        # add context param
        if fn.ctx_param_name is not None:
            if args is None:
                args = {fn.ctx_param_name: ctx}
            else:
                args[fn.ctx_param_name] = ctx
        if args is None:
            re = await fn.fn()
        re = await fn.fn(**args)
        time2 = datetime.datetime.now()
        # print(f"Time taken to execute the function: {time2 - time1}")
        return re

    def use_hitl(self, hitl: HITL):
        self._hitl = hitl

    def schema(self):
        """
        Find the wrapped tool functions and export them as yaml
        """
        return {
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

    async def get_screenshot(self) -> str | None:
        return None

    # Context manager
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
            ctx: Context | None = None,
    ) -> List[ChatCompletionToolMessageParam]:
        ...


class BaseAgentTool(BaseTool, ABC):
    @abstractmethod
    async def chat(
            self,
            ctx: Context,
            instruction: str,
    ) -> str:
        ...
