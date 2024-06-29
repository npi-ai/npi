"""This module contains the classes for the context and context message"""
import datetime
import uuid
import json
import asyncio
from typing import List, Union

from litellm.types.completion import (
    ChatCompletionMessageParam,
)
from playground import callback


# if TYPE_CHECKING:
#     from npiai.core import App


class ThreadMessage:
    """the message wrapper of a message in the context"""
    thread_id: str
    agent_id: str
    task: str
    msg_id: str
    response: str
    messages: List[Union[ChatCompletionMessageParam]]
    metadata: dict
    born_at: datetime.date  # RFC3339

    def __init__(self, agent_id: str, thread_id: str, task: str) -> None:
        self.agent_id = agent_id
        self.thread_id = thread_id
        self.task = task
        self.born_at = datetime.datetime.now()
        self.messages = []

    def append(self, msg: Union[ChatCompletionMessageParam]) -> None:
        """add a message to the context"""
        self.messages.append(msg)

    def set_result(self, result: str) -> None:
        """set the result of the message"""
        self.response = result

    def raw(self) -> List[ChatCompletionMessageParam]:
        """return the raw message"""
        return self.messages.copy()

    def extend(self, result: List[ChatCompletionMessageParam]):
        self.messages.extend(result)

    def plaintext(self) -> str:
        """convert the context message to plain text"""
        msgs = {
            "task": self.task,
            "response": self.response,
        }
        history = []
        for msg in self.messages:
            if isinstance(msg, dict):
                history.append(msg)
            elif msg.tool_calls:
                calls = []
                for tool_call in msg.tool_calls:
                    calls.append(
                        {
                            "id": tool_call.id,
                            "fn_name": tool_call.function.name,
                            "fn_arguments": json.loads(tool_call.function.arguments),
                        }
                    )
                history.append(calls)
            else:
                history.append(
                    {
                        "role": msg.role,
                        "content": msg.content,
                    }
                )
        msgs['history'] = history
        return json.dumps(msgs)


class Context:
    """the abstraction of chat context """
    __active_app: Union['App', None] = None
    __last_screenshot: str | None = None

    def __init__(self, instruction: str) -> None:
        self.id = str(uuid.uuid4())
        self.born_at = datetime.datetime.now()
        self.history: List[ThreadMessage | str] = []
        self.q = asyncio.Queue()
        self.instruction = instruction
        self.cb_dict: dict[str, callback.Callable] = {}
        self.__is_finished = False
        self.__result: str = ''
        self.__is_failed = False
        self.__failed_msg: str = ''

    def set_active_app(self, app: Union['App', None]):
        self.__active_app = app

    async def refresh_screenshot(self) -> str | None:
        """
        Refresh and return the latest screenshot of the running app.

        Returns:
            None if no screenshot is available or the screenshot stays unchanged.
            Otherwise, return the latest screenshot.
        """
        if not self.__active_app or self.is_finished():
            # TODO: raise errors?
            return None

        screenshot = await self.__active_app.get_screenshot()

        if screenshot == self.__last_screenshot:
            return None

        self.__last_screenshot = screenshot

        return screenshot

    async def send_msg(self, cb: callback.Callable) -> None:
        """send a message to the context"""
        self.cb_dict[cb.id()] = cb
        await self.q.put(cb)

    async def fetch_msg(self) -> callback.Callable:
        """receive a message"""
        while not self.is_failed() and not self.is_finished():
            try:
                item = self.q.get_nowait()
                if item:
                    return item
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.01)

    def get_callback(self, cb_id: str) -> callback.Callable:
        return self.cb_dict[cb_id]

    def finish(self, msg: str):
        self.__result = msg
        self.__is_finished = True
        self.__last_screenshot = None
        self.set_active_app(None)
        self.q.task_done()

    def failed(self, msg: str):
        self.__failed_msg = msg
        self.__is_failed = True
        self.q.task_done()

    def is_finished(self) -> bool:
        return self.__is_finished

    def get_result(self) -> str:
        return self.__result

    def is_failed(self) -> bool:
        return self.__is_failed

    def get_failed_msg(self) -> str:
        return self.__failed_msg

    def retrieve(self, msg: str) -> str:
        """retrieve the message from the context"""
        return msg

    def append(self, msg: ThreadMessage) -> None:
        """add a message to the context"""
        self.history.append(msg)

    def fork(self, task: str) -> ThreadMessage:
        """fork a child message, typically when call a new tools"""
        tm = ThreadMessage(
            agent_id=self.agent_id,
            thread_id=self.id, task=task
        )
        self.history.append(tm)
        return tm

    def plaintext(self) -> str:
        """convert the context to plain text"""
        msgs = []
        for msg in self.history:
            if isinstance(msg, ThreadMessage):
                return msg.plaintext()
            else:
                msgs.append(msg)

        return json.dumps(msgs)
