import json
import threading
import traceback
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

from npiai_proto import api_pb2_grpc, api_pb2
from npiai.utils import logger
from npiai.core import hitl


class App:
    __app_name: str
    __app_type: api_pb2.AppType
    __npi_endpoint: str
    stub: api_pb2_grpc.AppServerStub
    hitl_handler: hitl.HITLHandler = None

    def __init__(
        self,
        app_name: str,
        app_type: api_pb2.AppType,
        endpoint: str = "localhost:9140",
        hitl_handler: hitl.HITLHandler = None,
    ):
        self.__app_name = app_name
        if endpoint is None:
            endpoint = "localhost:9140"
        self.__npi_endpoint = endpoint
        self.__app_type = app_type
        channel = grpc.insecure_channel(self.__npi_endpoint)
        self.stub = api_pb2_grpc.AppServerStub(channel)
        self.hitl_handler = hitl_handler

    def tool_name(self):
        return self.__app_name

    def schema(self):
        try:
            resp = self.stub.GetAppSchema(
                api_pb2.AppSchemaRequest(
                    type=self.__app_type
                )
            )
        except Exception as e:
            logger.error(e)
            return None
        return json.loads(resp.schema)

    def chat(self, msg: str) -> str:
        resp = self.stub.Chat(
            api_pb2.Request(
                code=api_pb2.RequestCode.CHAT,
                chat_request=api_pb2.ChatRequest(
                    type=self.__app_type,
                    instruction=msg
                )
            )
        )
        while True:
            match resp.code:
                case api_pb2.ResponseCode.FINISHED:
                    return resp.chat_response.message
                case api_pb2.ResponseCode.MESSAGE:
                    logger.info(f'[{self.__app_name}]: Received message: {resp.chat_response.message}')
                    resp = self.stub.Chat(
                        api_pb2.Request(
                            code=api_pb2.RequestCode.FETCH,
                            request_id=str(uuid.uuid4()),
                            thread_id=resp.thread_id,
                            chat_request=api_pb2.ChatRequest(
                                type=self.__app_type,
                            )
                        )
                    )
                case api_pb2.ResponseCode.SUCCESS:
                    resp = self.stub.Chat(
                        api_pb2.Request(
                            code=api_pb2.RequestCode.FETCH,
                            request_id=str(uuid.uuid4()),
                            thread_id=resp.thread_id,
                            chat_request=api_pb2.ChatRequest(
                                type=self.__app_type,
                            )
                        )
                    )
                case api_pb2.ResponseCode.ACTION_REQUIRED:
                    resp = self.stub.Chat(self.__call_human(resp))
                case _:
                    raise Exception("Error: failed to call function")

    def hitl(self, handler: hitl.HITLHandler):
        self.hitl_handler = handler

    def __call_human(self, resp: api_pb2.Response) -> api_pb2.Request:
        human_resp = self.hitl_handler.handle(
            hitl.convert_to_hitl_request(
                req=resp.action_response,
                app_name=self.__app_name
            )
        )
        if human_resp is hitl.ACTION_APPROVED:
            result = "approved"
        else:
            result = "denied"
        return api_pb2.Request(
            code=api_pb2.RequestCode.ACTION_RESULT,
            request_id=str(uuid.uuid4()),
            thread_id=resp.thread_id,
            action_result_request=api_pb2.ActionResultRequest(
                action_id=resp.action_response.action_id,
                action_result=result,
            )
        )


class Agent:
    __agent_name: str
    __npi_endpoint: str
    __prompt: str
    __description: str
    __llm: OpenAI
    tool_choice: ChatCompletionToolChoiceOptionParam = "auto"
    fn_map: dict = {}
    hitl_handler: hitl.HITLHandler = None

    def __init__(
        self,
        agent_name: str,
        description: str,
        prompt: str,
        endpoint: str = None,
        llm: OpenAI = None,
        hitl_handler: hitl.HITLHandler = None,
    ):
        self.__agent_name = agent_name
        self.__description = description
        self.__prompt = prompt
        self.__npi_endpoint = endpoint
        self.__llm = llm
        self.hitl_handler = hitl_handler

    def use(self, *apps: App):
        for app in apps:
            # inherit HITL handler
            if app.hitl_handler is None:
                app.hitl_handler = self.hitl_handler
            app_name = app.tool_name()
            self.fn_map[app_name] = app

    def group(self, *agents: 'Agent'):
        for agent in agents:
            app_name = agent.__as_app().tool_name()
            self.fn_map[app_name] = agent

    def hitl(self, handler: hitl.HITLHandler):
        self.hitl_handler = handler

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
                logger.info(response_message.content + '\n')

            tool_calls = response_message.tool_calls

            if tool_calls is None:
                return response_message.content

            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                try:
                    res = self.__call(fn_name, args)
                    # logger.info(f"Response: {res}")
                    logger.debug(f'[{self.__agent_name}]: app `{fn_name}` returned: {res}')
                except Exception as e:
                    res = ''.join(traceback.format_exception(e))
                    logger.error(res)

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fn_name,
                        "content": res,
                    }
                )

    def when(self, task: str):
        running = True
        msg = f'When {task}'

        def _poll():
            nonlocal running
            while running:
                self.run(msg)

        def _stop():
            nonlocal running
            running = False

        thread = threading.Thread(target=_poll)
        # thread.daemon = True
        thread.start()

        return _stop

    def __call(self, fn_name: str, args: dict) -> str:
        call_msg = f'[{self.__agent_name}]: Calling {fn_name}({args})'
        logger.info(call_msg)

        if fn_name not in self.fn_map:
            raise Exception(f"Tool {fn_name} not found.")

        fn = self.fn_map[fn_name]
        return fn.chat(args['message'])

    def __tools(self) -> List[ChatCompletionToolParam]:
        tools = []
        for tool_name, tool in self.fn_map.items():
            tools.append(tool.schema())
        return tools

    def __as_app(self) -> App:
        return App(self.__agent_name, api_pb2.AppType.CHAT)
