"""The basic interface for NPi Tools"""

import dataclasses
import inspect
import json
import re
from abc import ABC
from typing import Dict, List, Optional, Any, Type, Annotated, get_args, get_origin
from textwrap import dedent

import yaml

from pydantic import Field, create_model
from litellm.types.completion import (
    ChatCompletionToolMessageParam,
    ChatCompletionMessageParam,
)
from litellm.types.utils import ChatCompletionMessageToolCall
from openai.types.chat import ChatCompletionToolParam

from npiai.core.base import BaseTool, BaseFunctionTool
from npiai.core.hitl import HITL
from npiai.types import FunctionRegistration, ToolFunction, Shot, ToolMeta, FromContext
from npiai.utils import (
    logger,
    sanitize_schema,
    parse_docstring,
    to_async_fn,
    is_template_str,
)
from npiai.context import Context
from npiai.constant import CTX_QUERY_POSTFIX

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

    def use_hitl(self, hitl: HITL):
        """
        Attach the given HITL handler to this tool and all its sub apps

        Args:
            hitl: HITL handler
        """
        super().use_hitl(hitl)

        for app in self._sub_tools:
            app.use_hitl(hitl)

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
            # share hitl handler
            if tool._hitl is None:
                tool.use_hitl(self._hitl)

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
            call_msg = f"[{self.name}]: Calling {fn_name}"

            if args:
                arg_list = ", ".join(f"{k}={json.dumps(v)}" for k, v in args.items())
                call_msg += f"({arg_list})"
            else:
                call_msg += "()"

            logger.info(call_msg)
            await session.send(call_msg)

            try:
                res = await self.exec(session, fn_name, args)
            except Exception as e:
                logger.error(e)
                res = f"Exception while executing {fn_name}: {e}"
                await session.send(res)

            logger.debug(f"[{self.name}]: function `{fn_name}` returned: {res}")

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

            params = list(inspect.signature(fn).parameters.values())
            docstr = parse_docstring(inspect.getdoc(fn))
            tool_name = tool_meta.name or fn.__name__
            tool_desc = tool_meta.description or docstr.description

            if not tool_desc:
                raise ValueError(
                    f"Unable to get the description of tool function `{fn}`"
                )

            # parse schema
            tool_model = tool_meta.model
            tool_schema = tool_meta.schema
            ctx_param_name = None
            ctx_variables = []

            if not tool_model and len(params) > 0:
                # get parameter descriptions
                param_descriptions = {}
                for p in docstr.params:
                    param_descriptions[p.arg_name] = p.description

                # get parameter field definitions
                param_fields = {}
                for p in params:
                    if p.annotation is Context:
                        ctx_param_name = p.name
                        continue

                    if get_origin(p.annotation) is Annotated:
                        # extract context variables
                        return_type, anno = get_args(p.annotation)
                        if isinstance(anno, FromContext):
                            ctx_variables.append(
                                dataclasses.replace(
                                    anno,
                                    name=p.name,
                                    return_type=return_type,
                                )
                            )

                            if is_template_str(anno.query):
                                param_fields[f"{p.name}{CTX_QUERY_POSTFIX}"] = (
                                    str,
                                    Field(
                                        default=anno.query,
                                        description=dedent(
                                            f"""
                                            This parameter is a query to retrieve information from the memory storage.
                                            For the following query, you should replace the strings surrounded by braces
                                            `{{}}` with the information from current context.
                                            
                                            Query: {anno.query}
                                            """
                                        ),
                                    ),
                                )
                            continue

                    param_fields[p.name] = (
                        p.annotation,
                        Field(
                            default=(
                                p.default
                                if p.default is not inspect.Parameter.empty
                                else ...
                            ),
                            description=param_descriptions.get(p.name, ""),
                        ),
                    )

                if len(param_fields):
                    tool_model = create_model(f"{tool_name}_model", **param_fields)

            if not tool_schema and tool_model:
                tool_schema = sanitize_schema(tool_model)

            # parse examples
            tool_few_shots = tool_meta.few_shots
            doc_shots = [m for m in docstr.meta if m.args == ["few_shots"]]

            if not tool_few_shots and len(doc_shots) > 0:
                tool_few_shots = []

                for shot in doc_shots:
                    items = re.findall(r"^\s*- ", shot.description, re.MULTILINE)
                    if len(items) == 1:
                        # remove leading '- ' to avoid indentation issues
                        shot_data = yaml.safe_load(
                            re.sub(r"^\s*- ", "", shot.description)
                        )
                    else:
                        shot_data = yaml.safe_load(shot.description)

                    if not isinstance(shot_data, list):
                        shot_data = [shot_data]

                    for d in shot_data:
                        tool_few_shots.append(Shot(**d))

            self._add_function(
                FunctionRegistration(
                    # wrap fn in an async wrapper
                    fn=to_async_fn(fn),
                    name=tool_name,
                    ctx_variables=ctx_variables,
                    ctx_param_name=ctx_param_name,
                    description=tool_desc.strip(),
                    schema=tool_schema,
                    model=tool_model,
                    few_shots=tool_few_shots,
                )
            )

    def _add_function(self, fn_reg: FunctionRegistration):
        if fn_reg.name in self._fn_map:
            raise Exception(f"Duplicate function: {fn_reg.name}")

        self._fn_map[fn_reg.name] = fn_reg
        self._tools.append(fn_reg.get_tool_param())
