from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam, ChatCompletionMessage
from npi.app.google.gmail.shared.function_registration import FunctionRegistration
from typing import List, Dict
import json
import os


class Agent:
    tools: List[ChatCompletionToolParam]
    fn_map: Dict[str, FunctionRegistration]
    model: str
    system_prompt: str
    client: OpenAI

    def __init__(
        self,
        model: str = None,
        api_key: str = None,
        system_prompt: str = None,
        function_list: List[FunctionRegistration] = None
    ):
        self.tools = []
        self.fn_map = {}
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = system_prompt

        if function_list:
            for fn_reg in function_list:
                self.register(fn_reg)

    def register(
        self,
        fn_reg: FunctionRegistration,
    ):
        if fn_reg.name in self.fn_map:
            return

        self.fn_map[fn_reg.name] = fn_reg

        tool: ChatCompletionToolParam = {
            'type': 'function',
            'function': {
                'name': fn_reg.name,
                'description': fn_reg.description,
            }
        }

        if fn_reg.Params is not None:
            tool['function']['parameters'] = fn_reg.Params.model_json_schema()

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
        tool_messages = self._parse_response(message, response_message)

        return prompts, response_message, tool_messages

    def _parse_response(self, prompt: str, response_message: ChatCompletionMessage):
        tool_calls = response_message.tool_calls
        tool_messages = []

        if not tool_calls:
            return tool_messages

        for tool_call in tool_calls:
            fn_name = tool_call.function.name
            fn_reg = self.fn_map[fn_name]
            args = json.loads(tool_call.function.arguments)
            print(f'Calling {fn_name}({args})')
            res = fn_reg.fn(fn_reg.Params(**args), self, prompt)
            tool_messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": fn_name,
                    "content": res,
                }
            )

        return tool_messages
