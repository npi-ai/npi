import asyncio
import uuid

from proto.python.api import api_pb2


class Callable:
    msg: str
    called: bool
    action: api_pb2.ActionResponse

    __id: str
    __type: api_pb2.ResponseCode = api_pb2.ResponseCode.MESSAGE
    __callback_result: str = ''

    def __init__(self, msg: str = None, action: api_pb2.ActionResponse = None):
        self.msg = msg
        self.called = False
        self.action = action
        if action:
            self.__type = api_pb2.ResponseCode.ACTION_REQUIRED
        self.__id = str(uuid.uuid4())

    def id(self):
        return self.__id

    def client_response(self):
        if self.__type == api_pb2.ResponseCode.MESSAGE:
            return api_pb2.ChatResponse(message=self.msg)
        elif self.__type == api_pb2.ResponseCode.ACTION_REQUIRED:
            return self.action
        return self.__type

    def type(self) -> api_pb2.ResponseCode:
        return self.__type

    def message(self) -> str:
        return self.msg

    def callback(self, msg: str):
        self.__callback_result = msg
        self.called = True

    async def wait(self) -> str:
        while not self.called:
            await asyncio.sleep(0.001)
        return self.__callback_result
