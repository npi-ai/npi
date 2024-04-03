from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam, ChatCompletionMessage
from npi.app.google.gmail.shared.parameter import Parameter
from typing import List, Dict, Callable, Any, Tuple, Type
import json

AgentFunction = Callable[['Agent', Parameter], Any]


class Agent:
    tools: List[ChatCompletionToolParam]
    fn_map: Dict[str, Tuple[AgentFunction, Type[Parameter]]]
    model: str
    system_prompt: str
    client: OpenAI

    def __init__(self, model: str, api_key: str, system_prompt: str = None):
        self.tools = []
        self.fn_map = {}
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = system_prompt

    def register(
        self,
        fn: Callable,
        description: str,
        name: str = None,
        Params: Type[Parameter] = None,
    ):
        if name is None:
            fn_name = f'{fn.__name__}_{hash(fn)}'
        else:
            fn_name = name

        if fn_name in self.fn_map:
            return

        self.fn_map[fn_name] = (fn, Params)

        tool: ChatCompletionToolParam = {
            'type': 'function',
            'function': {
                'name': fn_name,
                'description': description,
            }
        }

        if Params is not None:
            tool['function']['parameters'] = Params.model_json_schema()

        self.tools.append(tool)

    def chat(self, message: str):
        prompts = []

        if self.system_prompt:
            prompts.append(
                {
                    'role': 'system',
                    'content': self.system_prompt
                }
            )

        prompts.append(
            {
                'role': 'user',
                'content': message
            }
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=prompts,
            tools=self.tools,
            tool_choice='auto',
        )

        response_message = response.choices[0].message
        tool_messages = self._parse_response(response_message)

        return prompts, response_message, tool_messages

    def _parse_response(self, response_message: ChatCompletionMessage):
        tool_calls = response_message.tool_calls
        tool_messages = []

        if not tool_calls:
            return tool_messages

        for tool_call in tool_calls:
            fn_name = tool_call.function.name
            fn, Params = self.fn_map[fn_name]
            args = json.loads(tool_call.function.arguments)
            print(f'Calling {fn_name}({args})')
            res = fn(self, Params(**args))
            tool_messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": fn_name,
                    "content": res,
                }
            )

        return tool_messages
