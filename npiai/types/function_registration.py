from typing import Callable, Optional, Awaitable, List, Dict, Any, Type, TYPE_CHECKING
from dataclasses import dataclass, asdict, field

from openai.types.chat import ChatCompletionToolParam
from pydantic import BaseModel

from npiai.types.shot import Shot
from npiai.types.from_vector_db import FromVectorDB

if TYPE_CHECKING:
    from npiai import AgentTool

ToolFunction = Callable[..., Awaitable[Any]]


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
    # target agent for the `chat()` function
    calling_agent: Optional["AgentTool"] = None

    def is_agent(self):
        return self.calling_agent is not None

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

    def get_tool_param(self) -> ChatCompletionToolParam:
        tool: ChatCompletionToolParam = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
            },
        }

        if self.schema is not None:
            tool["function"]["strict"] = True
            tool["function"]["parameters"] = self.schema

        return tool
