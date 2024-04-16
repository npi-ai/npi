"""This module contains the classes for the thread and thread message"""
import datetime
import uuid
import json
import asyncio
from typing import List, Union

from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionMessage,
)

from npi.core import callback

from proto.python.api import api_pb2


class ThreadMessage:
    """the message wrapper of a message in the thread"""
    thread_id: str
    agent_id: str
    task: str
    msg_id: str
    response: str
    messages: List[Union[ChatCompletionMessageParam, ChatCompletionMessage]]
    metadata: dict
    born_at: datetime.date  # RFC3339

    def __init__(self, agent_id: str, thread_id: str, task: str) -> None:
        self.agent_id = agent_id
        self.thread_id = thread_id
        self.task = task
        self.born_at = datetime.datetime.now()
        self.messages = []

    def append(self, msg: Union[ChatCompletionMessageParam, ChatCompletionMessage]) -> None:
        """add a message to the thread"""
        self.messages.append(msg)

    def set_result(self, result: str) -> None:
        """set the result of the message"""
        self.response = result

    def raw(self) -> List[ChatCompletionMessageParam]:
        """return the raw message"""
        return self.messages.copy()

    def plaintext(self) -> str:
        """convert the thread message to plain text"""
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


class Thread:
    """the abstraction of chat context """
    agent_id: str
    id: str
    history: List[ThreadMessage | str]
    born_at: datetime.date
    q: asyncio.Queue[callback.Callable]
    instruction: str
    app_type: api_pb2.AppType

    __is_finished = False
    __result: str = ''

    def __init__(self, instruction: str, app_type: api_pb2.AppType) -> None:
        self.agent_id = 'default'
        self.id = str(uuid.uuid4())
        self.born_at = datetime.datetime.now()
        self.history = []
        self.q = asyncio.Queue()
        self.instruction = instruction
        self.app_type = app_type

    async def send_msg(self, cb: callback.Callable) -> None:
        await self.q.put(cb)

    async def fetch_msg(self) -> callback.Callable:
        """receive a message"""
        while True:
            try:
                item = self.q.get_nowait()
                if item:
                    return item
            except asyncio.QueueEmpty:
                if not self.is_finished():
                    await asyncio.sleep(0.01)
                else:
                    return None

    def callback(self, msg: str):
        pass

    def finish(self, msg: str):
        self.__result = msg
        self.__is_finished = True
        self.q.task_done()

    def failed(self, msg: str):
        pass

    def is_finished(self) -> bool:
        return self.__is_finished

    def get_result(self) -> str:
        return self.__result

    def ask(self, msg: str) -> str:
        """retrieve the message from the thread"""
        return msg

    def append(self, msg: ThreadMessage) -> None:
        """add a message to the thread"""
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
        """convert the thread to plain text"""
        msgs = []
        for msg in self.history:
            if isinstance(msg, ThreadMessage):
                return msg.plaintext()
            else:
                msgs.append(msg)

        return json.dumps(msgs)
