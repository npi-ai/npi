import json
from typing import Union, List

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)


class App:
    __app_name: str
    __npi_endpoint: str

    def __init__(self, app_name: str, endpoint: str):
        self.__app_name = app_name
        self.__npi_endpoint = endpoint

    def chat(self):
        pass

    def tool_name(self):
        return self.__app_name

    def schema(self):
        return {
            'type': 'app',
            'app': {
                'name': self.__app_name,
            }
        }

    def call(self, args: dict) -> str:
        pass

class Agent:
    __agent_name: str
    __npi_endpoint: str
    __prompt: str
    __description: str
    __llm: OpenAI
    tool_choice: ChatCompletionToolChoiceOptionParam = "auto"
    fn_map: dict = {}

    def __init__(self,
                 agent_name: str,
                 description: str,
                 prompt: str,
                 endpoint: str = None,
                 llm: OpenAI = None):
        self.__agent_name = agent_name
        self.__description = description
        self.__prompt = prompt
        self.__npi_endpoint = endpoint
        self.__llm = llm

    def use(self, *tools: Union['App']):
        for app in tools:
            app_name = app.tool_name()
            self.fn_map[app_name] = app

    def run(self, msg: str) -> str:

        messages = [ChatCompletionSystemMessageParam(
            content=self.__prompt,
            role="system",
        ), ChatCompletionUserMessageParam(
            content=msg,
            role="user",
        )]

        while True:
            # TODO: stream response
            response = await self.__llm.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                tools=self.__tools(),
                tool_choice=self.tool_choice,
                max_tokens=4096,
            )
            response_message = response.choices[0].message

            messages.append(response_message)

            if response_message.content:
                print(response_message.content + '\n')

            tool_calls = response_message.tool_calls

            if tool_calls is None:
                return response_message.content

            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                res = self.__call(fn_name, args)
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fn_name,
                        "content": res,
                    }
                )
                # self.on_round_end(message)

    def __call(self, fn_name: str, args: dict) -> str:
        call_msg = f'Calling {fn_name}({args})'
        print(call_msg)
        fn = self.fn_map[fn_name]
        if fn is not None:
            return fn.call(args)
        return "Error: tool not found"

    def __tools(self) -> List[ChatCompletionToolParam]:
        tools = []
        for tool_name, tool in self.fn_map.items():
            tools.append(tool.schema())
        return tools
