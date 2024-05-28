import asyncio
import functools
import inspect
import ast
import re
from dataclasses import asdict
from textwrap import dedent
from pydantic import BaseModel, Field, create_model
from typing import Optional, List, Callable, Dict, Any

import yaml
from openai.types.chat import ChatCompletionMessageToolCall, ChatCompletionToolParam

from npiai.types import ToolFunction, Shot, FunctionRegistration
from npiai.utils import parse_docstring


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
    model: str
    provider: str
    version: str
    endpoint: str

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
        model: str | None = None,
        provider: str | None = None,
        version: str | None = None,
        endpoint: str | None = None
    ):
        self.name = name
        self.description = description
        self.model = model
        if provider is None:
            self.provider = 'private'
        else:
            self.provider = provider

        self.version = version
        self.endpoint = endpoint
        self._functions = []
        self._fn_map = {}
        self._tools = []

    def _register_function(self, fn_reg: FunctionRegistration):
        self._functions.append(fn_reg)
        self._fn_map[fn_reg.name] = fn_reg
        self._tools.append(fn_reg.as_tool())

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
            @functools.wraps(fn)
            async def tool_wrapper(*args, **kwargs):
                res = fn(*args, **kwargs)
                if asyncio.iscoroutine(res):
                    return await res
                return res

            self._register_function(
                FunctionRegistration(
                    fn=tool_wrapper,
                    name=tool_name,
                    description=tool_desc.strip(),
                    code=extract_code(fn),
                    schema=tool_schema,
                    few_shots=tool_few_shots,
                )
            )

            return tool_wrapper

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

    def server(self, port: int):
        pass

    def call(self, messages: List[ChatCompletionMessageToolCall]):
        pass

    async def async_call(self):
        pass

    def add(self, *tools: 'NPi'):
        for tool in tools:
            for fn_reg in tool.functions:
                data = asdict(fn_reg)
                data['name'] = f'{tool.name}__{fn_reg.name}'
                scoped_fn_reg = FunctionRegistration(**data)
                self._register_function(scoped_fn_reg)

    def chat(self, msg: str) -> str:
        pass

    def debug(self, fn_name: str, params: Dict[str, Any] = None):
        if fn_name not in self._fn_map:
            raise RuntimeError("function not found")

        tool = self._fn_map[fn_name]
        res = tool.fn(**params) if params else tool.fn()
        if asyncio.iscoroutine(res):
            return asyncio.run(res)
        return res
