"""The basic interface for NPi Tools"""

import dataclasses
import inspect
import json
from abc import ABC
from typing import Dict, List, Optional, Any, Type

from litellm.types.completion import (
    ChatCompletionToolMessageParam,
    ChatCompletionMessageParam,
)
from litellm.types.utils import ChatCompletionMessageToolCall
from openai.types.chat import ChatCompletionToolParam

from npiai.context import Context
from npiai.core.base import BaseTool, BaseFunctionTool
from npiai.types import FunctionRegistration, ToolFunction, Shot, ToolMeta
from npiai.utils import parse_npi_function

__NPI_TOOL_ATTR__ = "__NPI_TOOL_ATTR__"


def function(
    tool_fn: ToolFunction = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    schema: Dict[str, Any] = None,
    model: Optional[Type[BaseTool]] = None,
    few_shots: Optional[List[Shot]] = None,
):
    """
    NPi Tool decorator for functions

    Args:
        tool_fn: Tool function. This value will be set automatically.
        name: Tool name. The tool function name will be used if not given.
        description: Tool description. This value will be inferred from the tool's docstring if not given.
        schema: Tool parameters schema. This value will be inferred from the tool's type hints if not given.
        model: Pydantic model for tool schema. This value will be built from the schema if not given.
        few_shots: Predefined working examples.

    Returns:
        Wrapped tool function that will be registered on the tools class
    """

    def decorator(fn: ToolFunction):
        setattr(
            fn,
            __NPI_TOOL_ATTR__,
            ToolMeta(
                name=name,
                description=description,
                schema=schema,
                model=model,
                few_shots=few_shots,
            ),
        )

        return fn

    # called as `@function`
    if callable(tool_fn):
        return decorator(tool_fn)

    # called as `@function(...)`
    return decorator


class FunctionTool(BaseFunctionTool, ABC):
    """The basic interface for the natural language programming interface"""

    _tools: List[ChatCompletionToolParam]
    _fn_map: Dict[str, FunctionRegistration]
    _sub_tools: List[BaseTool]

    _started: bool = False

    @property
    def functions(self):
        return list(self._fn_map.values())

    @property
    def sub_tools(self):
        return self._sub_tools

    def __init__(self):
        super().__init__()

        self._tools = []
        self._fn_map = {}
        self._sub_tools = []

        self._register_tools()

    def unpack_functions(self) -> List[FunctionRegistration]:
        return list(self._fn_map.values())

    async def start(self):
        """Start the tools"""
        if not self._started:
            self._started = True
            for tool in self._sub_tools:
                await tool.start()

    async def end(self):
        """Stop and dispose the tools"""
        if self._started:
            self._started = False
            for app in self._sub_tools:
                await app.end()

    def add_tool(
        self,
        *tools: BaseTool,
    ):
        for tool in tools:
            self._sub_tools.append(tool)

            for fn_reg in tool.unpack_functions():
                scoped_fn_reg = dataclasses.replace(
                    fn_reg, name=f"{tool.name}_{fn_reg.name}"
                )
                self._add_function(scoped_fn_reg)

    async def debug(
        self,
        session: Context | None = None,
        app_name: str = None,
        fn_name: str = None,
        args: Dict[str, Any] = None,
    ) -> str:
        if app_name:
            fn_name = f"{app_name}_{fn_name}"

        return await self.exec(session, fn_name, args)

    async def call(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
        session: Context | None = None,
    ) -> List[ChatCompletionMessageParam]:
        if session is None:
            session = Context()
        results: List[ChatCompletionToolMessageParam] = []

        for call in tool_calls:
            fn_name = call.function.name
            args = json.loads(call.function.arguments)

            try:
                res = await self.exec(session, fn_name, args)
            except Exception as e:
                res = f"Exception while executing {fn_name}: {e}"
                await session.send_error_message(res)

            await session.send_debug_message(
                f"[{self.name}]: function `{fn_name}` returned: {res}"
            )

            results.append(
                ChatCompletionToolMessageParam(
                    role="tool",
                    tool_call_id=call.id,
                    content=str(res),
                )
            )

        return results

    def _register_tools(self):
        """
        Find the wrapped tool functions and register them in this tools
        """
        for attr, fn in inspect.getmembers(
            self, lambda x: inspect.ismethod(x) or inspect.isfunction(x)
        ):
            tool_meta: ToolMeta | None = getattr(fn, __NPI_TOOL_ATTR__, None)

            if not callable(fn) or not tool_meta:
                continue

            fn_reg = parse_npi_function(fn, tool_meta)
            self._add_function(fn_reg)

    def _add_function(self, fn_reg: FunctionRegistration):
        if fn_reg.name in self._fn_map:
            raise Exception(f"Duplicate function: {fn_reg.name}")

        self._fn_map[fn_reg.name] = fn_reg
        self._tools.append(fn_reg.get_tool_param())
