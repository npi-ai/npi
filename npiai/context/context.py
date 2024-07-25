"""This module contains the classes for the context and context message"""
import datetime
import uuid
import asyncio
from typing import List, Union, Dict

from fastapi import Request
from litellm.types.completion import ChatCompletionMessageParam

from npiai.cloud import Client


class Task:
    """the message wrapper of a message in the context"""

    def __init__(self, goal: str) -> None:
        self.task_id = str(uuid.uuid4())
        self.goal = goal
        self.born_at = datetime.datetime.now()
        self.dialogues: List[Union[ChatCompletionMessageParam]] = []
        self.response: str
        self._session: 'Context' | None = None

    async def step(self, msgs: List[Union[ChatCompletionMessageParam]]) -> None:
        """add a message to the context"""
        self.dialogues.extend(msgs)

        # for msg in msgs:
        #     if msg.get('content'):
        #         await self._session.send(callback.Callable(msg.get('content')))

    def set_session(self, session: 'Context') -> None:
        self._session = session

    def conversations(self) -> List[ChatCompletionMessageParam]:
        """return the raw message"""
        return self.dialogues.copy()


class Context:
    __last_screenshot: str | None = None

    def __init__(self, req: Request | None = None, client: Client | None = None) -> None:
        if not client:
            client = Client(access_token=req.headers.get('x-npi-access-token'))
        self.client = client
        self.id = str(uuid.uuid4())
        self.q = asyncio.Queue()
        self.__is_finished = False
        self.__result: str = ''
        self.__is_failed = False
        self.__failed_msg: str = ''
        self.__active_tool = None
        self.__request = req
        self.__user_id = req.headers.get("x-npi-user-id")

    def credentials(self, app_code: str) -> Dict[str, str]:
        return self.client.get_credentials(app_code)

    def entry(self):
        pass

    def exit(self):
        pass

    def with_task(self, task: Task) -> 'Context':
        task.set_session(self)
        return self

    def fork(self, task: Task) -> 'Context':
        """fork a child message, typically when call a new tools"""
        return self.with_task(task)

    async def refresh_screenshot(self) -> str | None:
        """
        Refresh and return the latest screenshot of the running tools.

        Returns:
            None if no screenshot is available or the screenshot stays unchanged.
            Otherwise, return the latest screenshot.
        """
        if not self.__active_tool or self.is_finished():
            return None

        screenshot = await self.__active_tool.get_screenshot()

        if screenshot == self.__last_screenshot:
            return None

        self.__last_screenshot = screenshot

        return screenshot

    async def send(self, cb) -> None:
        """send a message to the context"""
        # self.cb_dict[cb.id()] = cb
        await self.q.put(cb)

    async def fetch(self):
        """receive a message"""
        while not self.is_failed() and not self.is_finished():
            try:
                item = self.q.get_nowait()
                if item:
                    return item
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.01)

    def get_callback(self, cb_id: str):
        pass
        # return self.cb_dict[cb_id]

    def finish(self, msg: str):
        self.__result = msg
        self.__is_finished = True
        self.__last_screenshot = None
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
        pass

    def bind(self, tool):
        self.__active_tool = tool

    def get_tool(self):
        return self.__active_tool
