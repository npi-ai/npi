import asyncio
import uuid

from playground.proto import playground_pb2


class ActionResult:

    def __init__(self, result: playground_pb2.ActionResultRequest):
        self.result = result

    def is_approved(self):
        return self.result.action_result != "denied"

    def has_message(self):
        pass


class Callable:

    def __init__(
        self, msg: str = None, action: playground_pb2.ActionRequiredResponse = None
    ):
        self.msg = msg
        self.called = False
        self.action = action
        if action:
            self.__type = playground_pb2.ResponseCode.ACTION_REQUIRED
        else:
            self.__type = playground_pb2.ResponseCode.MESSAGE
        self.__id = str(uuid.uuid4())
        self.__future = asyncio.get_event_loop().create_future()

    def id(self):
        return self.__id

    def client_response(self):
        if self.__type == playground_pb2.ResponseCode.MESSAGE:
            return playground_pb2.ChatResponse(message=self.msg)
        elif self.__type == playground_pb2.ResponseCode.ACTION_REQUIRED:
            return self.action
        return self.__type

    def type(self) -> playground_pb2.ResponseCode:
        return self.__type

    def message(self) -> str:
        return self.msg

    def callback(self, result: playground_pb2.ActionResultRequest):
        self.__future.set_result(result)

    async def wait(self) -> ActionResult:
        req = await self.__future
        return ActionResult(req)
