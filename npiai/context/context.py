"""This module contains the classes for the context and context message"""

import asyncio
import datetime
import uuid
from typing import List, Union, Dict, TYPE_CHECKING, Literal

from litellm.types.completion import ChatCompletionMessageParam

from npiai.types import RuntimeMessage

from .memory import VectorDBMemory

if TYPE_CHECKING:
    from npiai.core import BaseTool, HITL


class Task:
    """the message wrapper of a message in the context"""

    def __init__(self, goal: str) -> None:
        self.task_id = str(uuid.uuid4())
        self.goal = goal
        self.born_at = datetime.datetime.now()
        self.dialogues: List[Union[ChatCompletionMessageParam]] = []
        self.response: str
        self._session: Union["Context", None] = None

    async def step(self, msgs: List[Union[ChatCompletionMessageParam]]) -> None:
        """add a message to the context"""
        self.dialogues.extend(msgs)

        # for msg in msgs:
        #     if msg.get('content'):
        #         await self._session.send(callback.Callable(msg.get('content')))

    def set_session(self, session: "Context") -> None:
        self._session = session

    def conversations(self) -> List[ChatCompletionMessageParam]:
        """return the raw message"""
        return self.dialogues.copy()


class Context:
    id: str
    vector_db: VectorDBMemory

    _q: asyncio.Queue[RuntimeMessage]
    _is_finished: bool
    _is_failed: bool
    _result: str
    _failed_msg: str
    _last_screenshot: str | None
    _active_tool: Union["BaseTool", None]
    _hitl: Union["HITL", None]

    @property
    def hitl(self) -> HITL:
        if self._hitl is None:
            raise AttributeError("HITL handler has not been set")

        return self._hitl

    def __init__(
        self,
    ) -> None:
        self.id = str(uuid.uuid4())
        self._q = asyncio.Queue()
        self._is_finished = False
        self._result = ""
        self._is_failed = False
        self._failed_msg = ""
        self._last_screenshot = None
        self._active_tool = None
        self._hitl = None
        self._vector_db = VectorDBMemory(context_id=self.id)

    def use_hitl(self, hitl: "HITL") -> None:
        self._hitl = hitl

    # @abstractmethod
    # NOTE: this method should not be abstract
    # since we need to create an empty context when running locally
    # SEE: FunctionTool::call()
    def credentials(self, app_code: str) -> Dict[str, str]:
        return {}

    def entry(self):
        pass

    def exit(self):
        pass

    def with_task(self, task: Task) -> "Context":
        task.set_session(self)
        return self

    def fork(self, task: Task) -> "Context":
        """fork a child message, typically when call a new tools"""
        return self.with_task(task)

    async def send(self, msg: RuntimeMessage):
        """send a message to the context"""
        await self._q.put(msg)

    async def send_tool_message(self, message: str):
        await self.send(
            {
                "type": "message",
                "message": message,
                "id": str(uuid.uuid4()),
            }
        )

    async def send_execution_result(self, tool_call_id: str, result: str):
        await self.send(
            {
                "type": "execution_result",
                "result": result,
                "tool_call_id": tool_call_id,
                "id": str(uuid.uuid4()),
            }
        )

    async def send_debug_message(self, message: str):
        await self.send(
            {
                "type": "debug",
                "message": message,
                "id": str(uuid.uuid4()),
            }
        )

    async def send_error_message(self, message: str):
        await self.send(
            {
                "type": "error",
                "message": message,
                "id": str(uuid.uuid4()),
            }
        )

    async def send_screenshot(self, screenshot: str):
        # avoid sending duplicates
        if screenshot == self._last_screenshot:
            return

        await self.send(
            {
                "type": "screenshot",
                "screenshot": screenshot,
                "id": str(uuid.uuid4()),
            }
        )

        self._last_screenshot = screenshot

    async def send_hitl_action(self, action: Literal["input", "confirm"], message: str):
        await self.send(
            {
                "type": "hitl",
                "action": action,
                "message": message,
                "id": str(uuid.uuid4()),
            }
        )

    async def fetch(self) -> RuntimeMessage:
        """receive a message"""
        while not self.is_failed() and not self.is_finished():
            try:
                item = self._q.get_nowait()
                if item:
                    return item
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.01)

    def finish(self, msg: str):
        self._result = msg
        self._is_finished = True
        self._last_screenshot = None
        self._q.task_done()

    def failed(self, msg: str):
        self._failed_msg = msg
        self._is_failed = True
        self._q.task_done()

    def is_finished(self) -> bool:
        return self._is_finished

    def get_result(self) -> str:
        return self._result

    def is_failed(self) -> bool:
        return self._is_failed

    def get_failed_msg(self) -> str:
        return self._failed_msg

    def bind(self, tool: "BaseTool"):
        self._active_tool = tool

    def get_tool(self) -> Union["BaseTool", None]:
        return self._active_tool
