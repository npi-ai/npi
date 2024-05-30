import asyncio
import functools
import inspect
import ast
import json
import os
import re
from dataclasses import asdict
from textwrap import dedent
from pydantic import BaseModel, Field, create_model
from typing import Optional, List, Callable, Dict, Any, Callable, Awaitable

import yaml
from openai.types.chat import (
    ChatCompletionMessageToolCall,
    ChatCompletionToolParam,
    ChatCompletionToolMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from npiai.types import ToolFunction, Shot, FunctionRegistration
from npiai.utils import parse_docstring, logger, to_async_fn
from npiai.llm import LLM, OpenAI
from .hooks import Hooks


def str_presenter(dumper, data):
    """
    Configures yaml for dumping multiline strings
    Ref: https://github.com/yaml/pyyaml/issues/240#issuecomment-1018712495
    """
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)  # to use with safe_dum


def extract_code(fn: Callable) -> str:
    expr = dedent(inspect.getsource(fn))
    doc = inspect.getdoc(fn)

    # remove docstring
    if doc:
        expr = re.sub(r'(?P<quotes>[\'"]{3})\s*' + doc + r'\s*(?P=quotes)', '', expr)

    tree = ast.parse(expr)

    ast_fn = tree.body[0]

    # remove @npi_tool decorator from code
    # TODO: ast tree traversal
    if isinstance(ast_fn, ast.FunctionDef):
        for i, decorator in enumerate(ast_fn.decorator_list):
            attr = None

            if isinstance(decorator, ast.Attribute):
                attr = decorator
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                attr = decorator.func

            if attr and attr.attr == 'function':
                ast_fn.decorator_list.pop(i)
                break

    return ast.unparse(tree)


def sanitize_schema(model: BaseModel) -> Dict[str, Any]:
    schema = model.model_json_schema()

    # remove unnecessary title
    schema.pop('title', None)

    for prop in schema.get('properties', {}).values():
        prop.pop('title', None)

        # use a more compact format for optional fields
        if 'anyOf' in prop and len(prop['anyOf']) == 2 and prop['anyOf'][1]['type'] == 'null':
            # copy the first type definition to props
            t = prop['anyOf'][0]
            for k, v in t.items():
                prop[k] = v

            prop.pop('anyOf', None)

            if prop.get('default') is None:
                prop.pop('default', None)

    # remove empty properties
    if len(schema.get('properties', {})) == 0:
        schema.pop('properties', None)

    return schema


class NPi:
    name: str
    description: str
    llm: LLM
    provider: str
    version: str
    endpoint: str

    hooks: Hooks

    _functions: List[FunctionRegistration]
    _fn_map: Dict[str, FunctionRegistration]
    _tools: List[ChatCompletionToolParam]

    @property
    def tools(self):
        return self._tools

    @property
    def functions(self):
        return self._functions

    def __init__(
        self,
        name: str = 'default',
        description: str = '',
        llm: LLM | None = None,
        provider: str | None = None,
        version: str | None = None,
        endpoint: str | None = None
    ):
        self.name = name
        self.description = description
        self.llm = llm or OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), model='gpt-4o')
        if provider is None:
            self.provider = 'private'
        else:
            self.provider = provider

        self.version = version
        self.endpoint = endpoint
        self._functions = []
        self._fn_map = {}
        self._tools = []
        self.hooks = Hooks()

    def _register_function(self, fn_reg: FunctionRegistration):
        self._functions.append(fn_reg)
        self._fn_map[fn_reg.name] = fn_reg
        self._tools.append(fn_reg.as_tool())

    async def _exec(self, fn_name: str, args: Dict[str, Any] = None) -> str:
        if fn_name not in self._fn_map:
            raise RuntimeError(
                f'[{self.name}]: function `{fn_name}` not found. Available functions: {self._fn_map.keys()}'
            )

        tool = self._fn_map[fn_name]

        if args is None:
            return await tool.fn()

        return await tool.fn(**args)

    def function(
        self,
        tool_fn: ToolFunction = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schema: Dict[str, Any] = None,
        few_shots: Optional[List[Shot]] = None
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
            params = list(inspect.signature(fn).parameters.values())
            docstr = parse_docstring(inspect.getdoc(fn))
            tool_name = name or fn.__name__
            tool_desc = description or docstr.description

            if not tool_desc:
                raise ValueError(
                    f'Unable to get the description of tool function `{fn}`'
                )

            # parse schema
            tool_schema = schema

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
            tool_few_shots = few_shots
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

            # wrap fn in an async wrapper
            wrapped_fn = to_async_fn(fn)

            self._register_function(
                FunctionRegistration(
                    fn=wrapped_fn,
                    name=tool_name,
                    description=tool_desc.strip(),
                    code=extract_code(fn),
                    schema=tool_schema,
                    few_shots=tool_few_shots,
                )
            )

            return wrapped_fn

        # called as `@npi.function`
        if callable(tool_fn):
            return decorator(tool_fn)

        # called as `@npi.function(...)`
        return decorator

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
                'functions': [t.get_meta() for t in self._functions],
            }
        }

        with open(filename, 'w') as f:
            yaml.dump(data, f)

    def add(self, *tools: 'NPi'):
        for tool in tools:
            # add starting and ending callbacks to hooks
            self.hooks.on_start(tool._start)
            self.hooks.on_end(tool._end)

            # add functions
            for fn_reg in tool.functions:
                data = asdict(fn_reg)
                data['name'] = f'{tool.name}__{fn_reg.name}'
                scoped_fn_reg = FunctionRegistration(**data)
                self._register_function(scoped_fn_reg)

    def server(self, port: int):
        pass

    async def _call(self, tool_calls: List[ChatCompletionMessageToolCall]) -> List[ChatCompletionToolMessageParam]:
        results: List[ChatCompletionToolMessageParam] = []

        for call in tool_calls:
            fn_name = call.function.name
            args = json.loads(call.function.arguments)
            call_msg = f'[{self.name}]: Calling {fn_name}'

            if args:
                arg_list = ', '.join(f'{k}={v}' for k, v in args.items())
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

    async def _chat(self, msg: str) -> str:
        messages: List[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(
                role='system',
                content=self.description,
            ),
            ChatCompletionUserMessageParam(
                role='user',
                content=msg,
            ),
        ]

        while True:
            response = await self.llm.completion(
                messages=messages,
                tools=self.tools,
                tool_choice='auto',
                max_tokens=4096,
            )

            response_message = response.choices[0].message

            messages.append(response_message)

            if response_message.content:
                logger.info(response_message.content)

            tool_calls = response_message.get('tool_calls', None)

            if tool_calls is None:
                break

            results = await self._call(tool_calls)
            messages.extend(results)

        return response_message.content

    async def _debug(self, toolset: str = None, fn_name: str = None, args: Dict[str, Any] = None) -> str:
        if toolset:
            fn_name = f'{toolset}__{fn_name}'
        return await self._exec(fn_name, args)

    async def _start(self):
        await self.hooks.internal_start()

    async def _end(self):
        await self.hooks.internal_end()
