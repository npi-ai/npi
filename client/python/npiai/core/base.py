import json
from typing import Union, List
import grpc
import uuid

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)

from proto.python.api import api_pb2_grpc, api_pb2


class App:
    __app_name: str
    __app_type: api_pb2.AppType
    __npi_endpoint: str
    stub: api_pb2_grpc.AppServerStub

    def __init__(self, app_name: str, app_type: api_pb2.AppType, endpoint: str):
        self.__app_name = app_name
        self.__npi_endpoint = endpoint
        self.__app_type = app_type
        channel = grpc.insecure_channel(self.__npi_endpoint)
        self.stub = api_pb2_grpc.AppServerStub(channel)

    def tool_name(self):
        return self.__app_name

    def schema(self):
        try:
            resp = self.stub.GetAppSchema(api_pb2.AppSchemaRequest(
                type=self.__app_type
            ))
        except Exception as e:
            print(e)
            return None
        return json.loads(resp.schema)

    def chat(self, msg: str) -> str:
        resp = self.stub.Chat(api_pb2.Request(
            code=api_pb2.RequestCode.CHAT,
            chat_request=api_pb2.ChatRequest(
                type=self.__app_type,
                instruction=msg
            )
        ))
        while True:
            if resp.code is api_pb2.ResponseCode.SUCCESS:
                return resp.chat_response.message
            elif resp.code is api_pb2.ResponseCode.MESSAGE:
                print(resp.chat_response.message)
            elif resp.code is api_pb2.ResponseCode.SUCCESS:
                resp = self.stub.Chat(api_pb2.Request(
                    code=api_pb2.RequestCode.FETCH,
                    request_id=str(uuid.uuid4()),
                    thread_id=resp.thread_id,
                    chat_request=api_pb2.ChatRequest(
                        type=self.__app_type,
                    )
                ))
                continue
            elif resp.code is api_pb2.ResponseCode.ACTION_REQUIRED:
                ar = resp.action_response
                if ar.type is api_pb2.ActionType.HUMAN_FEEDBACK:
                    fb = ar.human_feedback
                    arr = api_pb2.ActionResultRequest(
                        action_id=ar.action_id,
                    )

                    if fb.type is api_pb2.HumanFeedbackActionType.INPUT:
                        arr.action_result = input(f"Action Required: {fb.notice}\n")

                    resp = self.stub.Chat(api_pb2.Request(
                        code=api_pb2.RequestCode.FETCH,
                        request_id=str(uuid.uuid4()),
                        thread_id=resp.thread_id,
                        chat_request=api_pb2.ChatRequest(
                            type=self.__app_type,
                        )
                    ))
                    continue
            else:
                return "Error: failed to call function"
        return resp.chat_response.message


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
            response = self.__llm.chat.completions.create(
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
            return fn.chat(args['message'])
        return "Error: tool not found"

    def __tools(self) -> List[ChatCompletionToolParam]:
        tools = []
        for tool_name, tool in self.fn_map.items():
            tools.append(tool.schema())
        return tools
