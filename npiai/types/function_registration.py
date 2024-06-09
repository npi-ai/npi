from typing import Callable, Optional, Awaitable, List, Dict, Any
from dataclasses import dataclass, asdict

from openai.types.chat import ChatCompletionToolParam

from npiai.types.shot import Shot

ToolFunction = Callable[..., Awaitable[str]]


@dataclass(frozen=True)
class FunctionRegistration:
    fn: ToolFunction
    description: str
    name: str
    schema: Optional[Dict[str, Any]] = None
    few_shots: Optional[List[Shot]] = None

    def get_meta(self):
        return {
            'description': self.description,
            'name': self.name,
            'parameters': self.schema,
            'fewShots': [asdict(ex) for ex in self.few_shots] if self.few_shots else None,
        }

    def get_tool_param(self) -> ChatCompletionToolParam:
        tool: ChatCompletionToolParam = {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
            }
        }

        if self.schema is not None:
            tool['function']['parameters'] = self.schema

        return tool
