from typing import Callable, Optional, Awaitable, List, Dict, Any, Type
from dataclasses import dataclass, asdict, field

from openai.types.chat import ChatCompletionToolParam
from pydantic import BaseModel

from npiai.types.shot import Shot
from npiai.types.from_context import FromVectorDB

ToolFunction = Callable[..., Awaitable[Any]]

__EMPTY_PARAMS__ = {"type": "object", "properties": {}}


@dataclass(frozen=True)
class FunctionRegistration:
    fn: ToolFunction
    description: str
    name: str
    ctx_variables: List[FromVectorDB] = field(default_factory=list)
    ctx_param_name: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None
    model: Optional[Type[BaseModel]] = None
    few_shots: Optional[List[Shot]] = None

    def get_meta(self):
        # params = {}
        #
        # for name in self.schema:
        #     # remove context variable queries
        #     if not name.endswith(CTX_QUERY_POSTFIX):
        #         params[name] = self.schema[name]

        return {
            "description": self.description,
            "name": self.name,
            "parameters": self.schema,
            "fewShots": (
                [asdict(ex) for ex in self.few_shots] if self.few_shots else None
            ),
        }

    def get_tool_param(self, strict: bool = True) -> ChatCompletionToolParam:
        tool: ChatCompletionToolParam = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": (
                    self.schema if self.schema is not None else __EMPTY_PARAMS__
                ),
            },
        }

        if self.schema is not None and strict:
            tool["function"]["strict"] = True
            # tool["function"]["parameters"] = self.schema

        return tool
