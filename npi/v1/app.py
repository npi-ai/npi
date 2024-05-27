import asyncio
import functools
import inspect
from textwrap import dedent
from typing import Optional, Type, List

import yaml

from npi.v1.types import Parameters, ToolFunction, Shot, FunctionRegistration


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


class App:
    name: str
    description: str
    provider: str
    tools: List[FunctionRegistration]

    def __init__(self, name: str, description: str, provider: str):
        self.name = name
        self.description = description
        self.provider = provider
        self.tools = []

    def npi_tool(
        self,
        tool_fn: ToolFunction = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        Params: Optional[Type[Parameters]] = None,
        few_shots: Optional[List[Shot]] = None
    ):
        """
        NPi Tool decorator for functions

        Args:
            tool_fn: Tool function. This value will be set automatically.
            name: Tool name. The tool function name will be used if not given.
            description: Tool description. This value will be inferred from the tool's docstring if not given.
            Params: Tool parameters factory. This value will be inferred from the tool's type hints if not given.
            few_shots: Predefined working examples.

        Returns:
            Wrapped tool function that will be registered on the app class
        """

        def decorator(fn: ToolFunction):
            params = list(inspect.signature(fn).parameters.values())
            params_count = len(params)

            if params_count > 1:
                raise TypeError(
                    f'Tool function `{fn.__name__}` should have at most 1 parameter, got {params_count}'
                )

            ParamsClass: Type[Parameters] | None = Params

            if params_count == 1:
                # this method is likely to receive a Parameter object
                ParamsClass = Params or params[0].annotation

                if not ParamsClass or not issubclass(ParamsClass, Parameters):
                    raise TypeError(
                        f'Tool function `{fn.__name__}`\'s parameter should have type {type(Parameters)}, got {type(ParamsClass)}'
                    )

            tool_desc = description or fn.__doc__

            if not tool_desc:
                raise ValueError(
                    f'Unable to get the description of tool function `{fn}`'
                )

            # wrap fn in an async wrapper
            @functools.wraps(fn)
            async def tool_wrapper(*args, **kwargs):
                res = fn(*args, **kwargs)
                if asyncio.iscoroutine(res):
                    return await res
                return res

            tool_name = name or fn.__name__

            self.tools.append(
                FunctionRegistration(
                    fn=tool_wrapper,
                    name=tool_name,
                    description=tool_desc.strip(),
                    code=dedent(inspect.getsource(fn)),
                    Params=ParamsClass,
                    few_shots=few_shots,
                )
            )

            return tool_wrapper

        # called as `@app.npi_tool`
        if callable(tool_fn):
            return decorator(tool_fn)

        # called as `@app.npi_tool(...)`
        return decorator

    def export_tools(self, filename: str):
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
                'functions': [t.get_meta() for t in self.tools],
            }
        }

        with open(filename, 'w') as f:
            yaml.dump(data, f)
