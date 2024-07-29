import functools
from typing import List, Callable

from langchain_core.tools import BaseToolkit, StructuredTool
from langchain_core.pydantic_v1 import create_model, PrivateAttr, Field

from npiai.core import BaseTool as NPiBaseTool
from npiai.context import Context


def unwrap_context(func: Callable, ctx_param_name: str | None) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if ctx_param_name:
            # create an empty context for tools
            kwargs[ctx_param_name] = Context()
        return await func(*args, **kwargs)

    return wrapper


class NPiLangChainToolkit(BaseToolkit):
    _tools: List[StructuredTool] = PrivateAttr()

    def __init__(self, npi_tool: NPiBaseTool):
        BaseToolkit.__init__(self)
        self._tools = []

        for fn_reg in npi_tool.unpack_functions():
            # remove ctx param
            fn = unwrap_context(fn_reg.fn, fn_reg.ctx_param_name)
            # recreate pydantic-v1 compatible model
            params = {}

            if fn_reg.model:
                for name, field in fn_reg.model.model_fields.items():
                    if field.default and not field.is_required():
                        field_v1 = Field(
                            default=field.default,
                            description=field.description,
                        )
                    else:
                        field_v1 = Field(description=field.description)
                    params[name] = (field.annotation, field_v1)

            schema_model_v1 = create_model(
                f"{fn_reg.name}__model",
                **params,
            )

            self._tools.append(
                StructuredTool.from_function(
                    coroutine=fn,
                    name=fn_reg.name,
                    description=fn_reg.description,
                    args_schema=schema_model_v1,
                    infer_schema=False,
                )
            )

    def get_tools(self) -> List[StructuredTool]:
        return self._tools
