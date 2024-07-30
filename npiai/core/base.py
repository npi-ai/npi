from abc import ABC, abstractmethod
from typing import List, Dict, Any

from litellm.types.completion import ChatCompletionToolMessageParam
from litellm.types.utils import ChatCompletionMessageToolCall
from openai.types.chat import ChatCompletionToolParam

from npiai.context import Context
from npiai.core.hitl import HITL
from npiai.types import FunctionRegistration
from npiai.constant import CTX_QUERY_POSTFIX


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    system_prompt: str = ""
    provider: str = "private"

    _fn_map: Dict[str, FunctionRegistration]
    _hitl: HITL | None

    @classmethod
    def from_context(cls, ctx: Context) -> "BaseTool":
        # bind the tool to the Context
        raise NotImplementedError(
            "subclasses must implement this method for npi cloud hosting"
        )

    @property
    def hitl(self) -> HITL:
        if self._hitl is None:
            raise AttributeError("HITL handler has not been set")

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
        if fn_name not in self._fn_map:
            raise RuntimeError(
                f"[{self.name}]: function `{fn_name}` not found. Available functions: {self._fn_map.keys()}"
            )

        if not args:
            args = {}

        fn = self._fn_map[fn_name]

        # add context param
        if fn.ctx_param_name is not None:
            args[fn.ctx_param_name] = ctx

        # add context variables
        for ctx_var in fn.ctx_variables:
            query = args.pop(f"{ctx_var.name}{CTX_QUERY_POSTFIX}", ctx_var.query)

            args[ctx_var.name] = await ctx.ask(
                query=query,
                return_type=ctx_var.return_type,
                constraints=ctx_var.constraints,
            )

        return await fn.fn(**args)

    def use_hitl(self, hitl: HITL):
        self._hitl = hitl

    def schema(self):
        """
        Find the wrapped tool functions and export them as yaml
        """
        return {
            "kind": "Function",
            "metadata": {
                "name": self.name,
                "description": self.description,
                "provider": self.provider,
            },
            "spec": {
                "runtime": {
                    "language": "python",
                    "version": "3.11",
                },
                "dependencies": [
                    {
                        "name": "npiai",
                        "version": "0.1.0",
                    }
                ],
                "functions": [t.get_meta() for t in self.unpack_functions()],
            },
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
    ) -> List[ChatCompletionToolMessageParam]: ...


class BaseAgentTool(BaseTool, ABC):
    @abstractmethod
    async def chat(
        self,
        ctx: Context,
        instruction: str,
    ) -> str: ...
