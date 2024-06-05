"""The basic interface for NPi Apps"""
import json
import inspect
import functools
import re
from dataclasses import asdict
from typing import Dict, List, Optional, Union, Any

import yaml
from pydantic import Field, create_model
# TODO: use llmlite typings
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletionMessageToolCall,
    ChatCompletionToolMessageParam,
)

from npiai.types import FunctionRegistration, ToolFunction, Shot, ToolMeta
from npiai.utils import logger, sanitize_schema, parse_docstring, to_async_fn
from npiai.core.base import BaseApp, NPiBase

__NPI_TOOL_ATTR__ = '__NPI_TOOL_ATTR__'


def npi_tool(
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
        Wrapped tool function that will be registered on the app class
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

    # called as `@npi_tool`
    if callable(tool_fn):
        return decorator(tool_fn)

    # called as `@npi_tool(...)`
    return decorator


class App(BaseApp):
    """The basic interface for the natural language programming interface"""

    name: str
    description: str
    system_role: Optional[str]
    provider: str

    _tools: List[ChatCompletionToolParam]
    _fn_map: Dict[str, FunctionRegistration]
    _sub_apps: List[NPiBase]

    _started: bool = False

    @property
    def tools(self):
        return self._tools

    @property
    def functions(self):
        return list(self._fn_map.values())

    @property
    def sub_apps(self):
        return self._sub_apps

    def __init__(
        self,
        name: str,
        description: str,
        system_role: str = None,
        provider: str = None,
    ):
        super().__init__()
        self.name = name
        self.description = description
        self.system_role = system_role
        self.provider = provider or 'private'
        self._tools = []
        self._fn_map = {}
        self._sub_apps = []

        self._register_tools()

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
                'functions': [t.get_meta() for t in self._fn_map.values()],
            }
        }

        with open(filename, 'w') as f:
            yaml.dump(data, f)

    def list_functions(self) -> List[FunctionRegistration]:
        return list(self._fn_map.values())

    async def start(self):
        """Start the app"""
        if not self._started:
            self._started = True
            for app in self._sub_apps:
                await app.start()

    async def end(self):
        """Stop and dispose the app"""
        if self._started:
            self._started = False
            for app in self._sub_apps:
                await app.end()

    def add(
        self,
        *tools: NPiBase,
    ):
        for tool in tools:
            self._sub_apps.append(tool)
            is_app = isinstance(tool, App)

            for fn_reg in tool.list_functions():
                if is_app:
                    data = asdict(fn_reg)
                    data['name'] = f'{tool.name}__{fn_reg.name}'
                    scoped_fn_reg = FunctionRegistration(**data)
                else:
                    scoped_fn_reg = fn_reg

                if scoped_fn_reg.name in self._fn_map:
                    raise Exception(f'Duplicate function: {scoped_fn_reg.name}')

                self._add_function(scoped_fn_reg)

    async def debug(self, app_name: str = None, fn_name: str = None, args: Dict[str, Any] = None) -> str:
        if app_name:
            fn_name = f'{app_name}__{fn_name}'
        return await self._exec(fn_name, args)

    async def call(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
    ) -> List[ChatCompletionToolMessageParam]:
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

            res = await self._exec(fn_name, args)

            logger.debug(f'[{self.name}]: function `{fn_name}` returned: {res}')

            results.append(
                ChatCompletionToolMessageParam(
                    role='tool',
                    tool_call_id=call.id,
                    content=res,
                )
            )

        return results

    async def _exec(self, fn_name: str, args: Dict[str, Any] = None) -> str:
        if fn_name not in self._fn_map:
            raise RuntimeError(
                f'[{self.name}]: function `{fn_name}` not found. Available functions: {self._fn_map.keys()}'
            )

        tool = self._fn_map[fn_name]

        try:
            if args is None:
                return await tool.fn()
            return await tool.fn(**args)
        except Exception as e:
            logger.error(e)
            return f'Error: {e}'

    def _register_tools(self):
        """
        Find the wrapped tool functions and register them in this app
        """
        for attr in dir(self):
            fn = getattr(self, attr)
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

            if not tool_schema and len(params) > 0:
                # get parameter descriptions
                param_descriptions = {}
                for p in docstr.params:
                    param_descriptions[p.arg_name] = p.description

                # get parameter field definitions
                param_fields = {}
                for p in params:
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
                    description=tool_desc.strip(),
                    schema=tool_schema,
                    few_shots=tool_few_shots,
                )
            )

    def _add_function(self, fn_reg: FunctionRegistration):
        self._fn_map[fn_reg.name] = fn_reg
        self._tools.append(fn_reg.get_tool_param())
