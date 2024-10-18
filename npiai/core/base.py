import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from litellm.types.completion import ChatCompletionToolMessageParam
from litellm.types.utils import ChatCompletionMessageToolCall
from openai.types.chat import ChatCompletionToolParam

from npiai.context import Context
from npiai.types import FunctionRegistration
from npiai.constant import CTX_QUERY_POSTFIX
from npiai.utils import logger


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    system_prompt: str = ""
    provider: str = "private"

    _fn_map: Dict[str, FunctionRegistration]

    def __init__(self):
        self._fn_map = {}

    @classmethod
    def from_context(cls, ctx: Context) -> "BaseTool":
        # bind the tool to the Context
        raise NotImplementedError(
            "subclasses must implement this method for npi cloud hosting"
        )

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

    async def exec(
        self,
        ctx: Context,
        fn_name: str,
        args: Dict[str, Any] = None,
    ) -> str:
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

            args[ctx_var.name] = await ctx.vector_db.retrieve(
                query=query,
                return_type=ctx_var.return_type,
                constraints=ctx_var.constraints,
            )

        if fn.model:
            non_optional_args = {}

            # if an optional field received `None`, remove it from args
            for k, v in args.items():
                if v is not None:
                    non_optional_args[k] = v
                    continue

                field = fn.model.model_fields.get(k, None)

                if field and field.is_required():
                    non_optional_args[k] = v
        else:
            non_optional_args = args

        # log call message
        call_msg = f"[{self.name}]: Calling {fn_name}"

        arg_list = ", ".join(
            f"{k}={json.dumps(v) if k is not fn.ctx_param_name else 'NPiContext'}"
            for k, v in non_optional_args.items()
        )
        call_msg += f"({arg_list})"

        logger.info(call_msg)
        await ctx.send_debug_message(call_msg)

        res = await fn.fn(**non_optional_args)

        return str(res)

    def schema(self):
        """
        Find the wrapped tool functions and export them as yaml
        """
        return {
            "kind": "Function",
            "metadata": {
                "name": self.name,
                "description": self.description,
                "system_prompt": self.system_prompt,
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
