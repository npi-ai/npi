"""The basic interface for NPi Apps"""
import asyncio
import dataclasses
import functools
import inspect
import json
import os
import re
import signal
import sys
from dataclasses import asdict
from typing import Dict, List, Optional, Any
import logging

import yaml
import uvicorn
from fastapi import HTTPException
from pydantic import Field, create_model
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from litellm.types.completion import ChatCompletionToolMessageParam
from litellm.types.utils import ChatCompletionMessageToolCall
from openai.types.chat import ChatCompletionToolParam

from npiai.core.base import BaseTool, BaseFunctionTool
from npiai.core.hitl import HITL
from npiai.types import FunctionRegistration, ToolFunction, Shot, ToolMeta
from npiai.utils import logger, sanitize_schema, parse_docstring, to_async_fn
from npiai.context import Context
from npiai.core import callback

__NPI_TOOL_ATTR__ = '__NPI_TOOL_ATTR__'


def function(
        tool_fn: ToolFunction = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schema: Dict[str, Any] = None,
        few_shots: Optional[List[Shot]] = None,
):
    """
    NPi Tool decorator for functions

    Args:
        tool_fn: Tool function. This value will be set automatically.
        name: Tool name. The tool function name will be used if not given.
        description: Tool description. This value will be inferred from the tool's docstring if not given.
        schema: Tool parameters schema. This value will be inferred from the tool's type hints if not given.
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
                few_shots=few_shots,
            )
        )

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper

    # called as `@function`
    if callable(tool_fn):
        return decorator(tool_fn)

    # called as `@function(...)`
    return decorator


class FunctionTool(BaseFunctionTool):
    """The basic interface for the natural language programming interface"""

    name: str
    description: str
    system_prompt: Optional[str]
    provider: str

    _tools: List[ChatCompletionToolParam]
    _fn_map: Dict[str, FunctionRegistration]
    _sub_tools: List[BaseTool]

    _started: bool = False

    @property
    def tools(self):
        return self._tools

    @property
    def functions(self):
        return list(self._fn_map.values())

    @property
    def sub_tools(self):
        return self._sub_tools

    def __init__(
            self,
            name: str,
            description: str,
            system_prompt: str = None,
            provider: str = None,
    ):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.provider = provider or 'private'
        self._tools = []
        self._fn_map = {}
        self._sub_tools = []

        self._register_tools()
        super().__init__(self.name, self.description, self.provider)

    def unpack_functions(self) -> List[FunctionRegistration]:
        return list(self._fn_map.values())

    def use_hitl(self, hitl: HITL):
        """
        Attach the given HITL handler to this tools and all its sub apps

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

    def server(self):
        """Start the server"""
        asyncio.run(self.start())
        if not bool(os.environ.get("NPIAI_TOOL_SERVER_MODE")):
            print("Server mode is disabled, if you want to run the server, set env NPIAI_TOOL_SERVER_MODE=true")
            print("Exiting...")
            return

        fapp = FastAPI()

        def convert_camel_to_snake(name: str) -> str:
            return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

        @fapp.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
        async def root(full_path: str, request: Request):
            method = convert_camel_to_snake(full_path)
            ctx = Context(instruction="")
            try:
                match request.method:
                    case "POST":
                        args = await request.json()
                        res = await self._exec(ctx, method, args)
                    case "GET":
                        args = {k: v for k, v in request.query_params.items()}
                        res = await self._exec(ctx, method, args)
                    case _:
                        return JSONResponse({'error': 'Method not allowed'}, status_code=405)
                try:
                    return JSONResponse(content=json.loads(res))
                except json.JSONDecodeError as e:
                    return res
            except Exception as e:
                logging.error(f"Failed to process request: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Internal Server Error")

        def signal_handler(sig, frame):
            print(f"Signal {sig} received, shutting down...")
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:  # 'RuntimeError: There is no current event loop...'
                loop = None

            tsk = loop.create_task(self.end())
            # while not tsk.done():
            #     time.sleep(1)
            print("Shutdown complete")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        # signal.signal(signal.SIGKILL, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        uvicorn.run(fapp, host="0.0.0.0", port=18000)

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
                scoped_fn_reg = dataclasses.replace(fn_reg, name=f'{tool.name}_{fn_reg.name}')
                self._add_function(scoped_fn_reg)

    async def debug(self, app_name: str = None, fn_name: str = None, args: Dict[str, Any] = None) -> str:
        if app_name:
            fn_name = f'{app_name}_{fn_name}'

        return await self._exec(Context(), fn_name, args)

    async def call(
            self,
            tool_calls: List[ChatCompletionMessageToolCall],
            ctx: Context = None,
    ) -> List[ChatCompletionToolMessageParam]:
        if ctx is None:
            ctx = Context('')

        results: List[ChatCompletionToolMessageParam] = []

        for call in tool_calls:
            fn_name = call.function.name
            args = json.loads(call.function.arguments)
            call_msg = f'[{self.name}]: Calling {fn_name}'

            if args:
                arg_list = ', '.join(f'{k}={json.dumps(v)}' for k, v in args.items())
                call_msg += f'({arg_list})'
            else:
                call_msg += '()'

            logger.info(call_msg)
            await ctx.send_msg(callback.Callable(call_msg))

            res = None
            try:
                res = await self._exec(ctx, fn_name, args)
            except Exception as e:
                logger.error(e)
                await ctx.send_msg(callback.Callable(f'Exception while executing {fn_name}: {e}'))

            logger.debug(f'[{self.name}]: function `{fn_name}` returned: {res}')

            results.append(
                ChatCompletionToolMessageParam(
                    role='tool',
                    tool_call_id=call.id,
                    content=res,
                )
            )

        return results

    async def _exec(self, ctx: Context, fn_name: str, args: Dict[str, Any] = None) -> str:
        if fn_name not in self._fn_map:
            raise RuntimeError(
                f'[{self.name}]: function `{fn_name}` not found. Available functions: {self._fn_map.keys()}'
            )

        tool = self._fn_map[fn_name]

        # add context param
        if tool.ctx_param_name is not None:
            if args is None:
                args = {tool.ctx_param_name: ctx}
            else:
                args[tool.ctx_param_name] = ctx
        print(tool)
        print(args)
        if args is None:
            return str(await tool.fn())
        return str(await tool.fn(**args))

    def _register_tools(self):
        """
        Find the wrapped tool functions and register them in this tools
        """
        for attr, fn in inspect.getmembers(self, lambda x: inspect.ismethod(x) or inspect.isfunction(x)):
            tool_meta: ToolMeta | None = getattr(fn, __NPI_TOOL_ATTR__, None)

            if not callable(fn) or not tool_meta:
                continue

            params = list(inspect.signature(fn).parameters.values())
            docstr = parse_docstring(inspect.getdoc(fn))
            tool_name = tool_meta.name or fn.__name__
            tool_desc = tool_meta.description or docstr.description

            if not tool_desc:
                raise ValueError(
                    f'Unable to get the description of tool function `{fn}`'
                )

            # parse schema
            tool_schema = tool_meta.schema
            ctx_param_name = None

            if not tool_schema and len(params) > 0:
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
                    param_fields[p.name] = (p.annotation, Field(
                        default=p.default if p.default is not inspect.Parameter.empty else ...,
                        description=param_descriptions.get(p.name, ''),
                    ))

                model = create_model(f'{tool_name}_model', **param_fields)
                tool_schema = sanitize_schema(model)

            # parse examples
            tool_few_shots = tool_meta.few_shots
            doc_shots = [m for m in docstr.meta if m.args == ['few_shots']]

            if not tool_few_shots and len(doc_shots) > 0:
                tool_few_shots = []

                for shot in doc_shots:
                    items = re.findall(r'^\s*- ', shot.description, re.MULTILINE)
                    if len(items) == 1:
                        # remove leading '- ' to avoid indentation issues
                        shot_data = yaml.safe_load(re.sub(r'^\s*- ', '', shot.description))
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
                    ctx_param_name=ctx_param_name,
                    description=tool_desc.strip(),
                    schema=tool_schema,
                    few_shots=tool_few_shots,
                )
            )

    def _add_function(self, fn_reg: FunctionRegistration):
        if fn_reg.name in self._fn_map:
            raise Exception(f'Duplicate function: {fn_reg.name}')

        self._fn_map[fn_reg.name] = fn_reg
        self._tools.append(fn_reg.get_tool_param())
