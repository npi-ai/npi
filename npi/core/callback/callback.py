import asyncio
import uuid

from npiai_proto import api_pb2


class ActionResult:

    def __init__(self, result: api_pb2.ActionResultRequest):
        self.result = result

    def is_approved(self):
        pass

    def has_message(self):
        pass


class Callable:

    def __init__(self, msg: str = None, action: api_pb2.ActionRequiredResponse = None):
        self.msg = msg
        self.called = False
        self.action = action
        if action:
            self.__type = api_pb2.ResponseCode.ACTION_REQUIRED
        self.__id = str(uuid.uuid4())
        self.__future = asyncio.get_event_loop().create_future()

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

    def callback(self, result: api_pb2.ActionResultRequest):
        self.__future.set_result(result)

    async def wait(self) -> ActionResult:
        req = await self.__future
        return ActionResult(req)
