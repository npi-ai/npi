import asyncio
import uuid
import datetime
from fastapi import Request
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

from litellm.types.completion import ChatCompletionMessageParam
from litellm.types.completion import ChatCompletionToolMessageParam
from litellm.types.utils import ChatCompletionMessageToolCall
from openai.types.chat import ChatCompletionToolParam

from npiai.types import FunctionRegistration
from npiai.core import callback
from npiai.core.hitl import HITL


class Task:
    """the message wrapper of a message in the context"""

    def __init__(self, goal: str) -> None:
        self.task_id = str(uuid.uuid4())
        self.goal = goal
        self.born_at = datetime.datetime.now()
        self.dialogues: List[Union[ChatCompletionMessageParam]] = []
        self.response: str
        self._session: 'Context' | None = None

    async def record(self, msgs: List[Union[ChatCompletionMessageParam]]) -> None:
        """add a message to the context"""
        self.dialogues.extend(msgs)

        for msg in msgs:
            if msg.get('content'):
                await self._session.send(callback.Callable(msg.get('content')))

    def set_session(self, session: 'Context') -> None:
        self._session = session

    def conversations(self) -> List[ChatCompletionMessageParam]:
        """return the raw message"""
        return self.dialogues.copy()


class Context:
    __last_screenshot: str | None = None

    def __init__(self, req: Request | None = None) -> None:
        # self._parent_session = parent
        # self._task = task
        self.id = str(uuid.uuid4())
        self.q = asyncio.Queue()
        self.cb_dict: dict[str, callback.Callable] = {}
        self.__is_finished = False
        self.__result: str = ''
        self.__is_failed = False
        self.__failed_msg: str = ''
        self.__active_tool: Union[BaseTool, None] = None
        self.__request = req

    def authorization(self) -> str:
        return self.__request.headers.get('Authorization')

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

    async def send(self, cb: callback.Callable) -> None:
        """send a message to the context"""
        self.cb_dict[cb.id()] = cb
        await self.q.put(cb)

    async def fetch(self) -> callback.Callable:
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

    @classmethod
    def from_request(cls, req: Request) -> 'Context':
        return Context(req=req)

    def bind(self, tool: Union['BaseTool', None]):
        self.__active_tool = tool

    def get_tool(self) -> Union['BaseTool', None]:
        return self.__active_tool


class BaseTool(ABC):

    def __init__(self, name: str = "", description: str = "", provider: str = 'npiai',
                 fn_map: Dict[str, FunctionRegistration] | None = None):
        self.name = name
        self.description = description
        self.provider = provider
        self._fn_map = fn_map or {}
        self._hitl: HITL | None = None
        # self._context = _context

    @property
    def hitl(self) -> HITL:
        if self._hitl is None:
            raise AttributeError('HITL handler has not been set')

        return self._hitl

    @property
    def tools(self) -> List[ChatCompletionToolParam]:
        fns = self.unpack_functions()
        result = []
        for fn in fns:
            result.append(fn.get_tool_param())
        return result

    @abstractmethod
    def unpack_functions(self) -> List[FunctionRegistration]:
        """Export the functions registered in the tools"""
        ...

    @abstractmethod
    async def start(self):
        """Start the tools"""
        ...

    @abstractmethod
    async def end(self):
        """Stop and dispose the tools"""
        ...

    @classmethod
    def from_context(cls, ctx: Context) -> 'BaseTool':
        # bind the tool to the Context
        raise NotImplementedError("subclasses must implement this method for npi cloud hosting")

    async def exec(self, ctx: Context, fn_name: str, args: Dict[str, Any] = None):
        time1 = datetime.datetime.now()

        if fn_name not in self._fn_map:
            raise RuntimeError(
                f'[{self.name}]: function `{fn_name}` not found. Available functions: {self._fn_map.keys()}'
            )

        fn = self._fn_map[fn_name]

        # add context param
        if fn.ctx_param_name is not None:
            if args is None:
                args = {fn.ctx_param_name: ctx}
            else:
                args[fn.ctx_param_name] = ctx
        if args is None:
            re = await fn.fn()
        re = await fn.fn(**args)
        time2 = datetime.datetime.now()
        print(f"Time taken to execute the function: {time2 - time1}")
        return re

    def use_hitl(self, hitl: HITL):
        self._hitl = hitl

    def schema(self):
        """
        Find the wrapped tool functions and export them as yaml
        """
        return {
            'kind': 'Function',
            'metadata': {
                'name': self.name,
                'description': self.description,
                'provider': self.provider,
            },
            'spec': {
                'runtime': {
                    'language': 'python',
                    'version': '3.11',
                },
                'dependencies': [{
                    'name': 'npiai',
                    'version': '0.1.0',
                }],
                'functions': [t.get_meta() for t in self.unpack_functions()],
            }
        }

    async def get_screenshot(self) -> str | None:
        return None

    # Context manager
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.end()


class BaseFunctionTool(BaseTool, ABC):
    @abstractmethod
    async def call(
            self,
            tool_calls: List[ChatCompletionMessageToolCall],
            ctx: Context | None = None,
    ) -> List[ChatCompletionToolMessageParam]:
        ...


class BaseAgentTool(BaseTool, ABC):
    @abstractmethod
    async def chat(
            self,
            ctx: Context,
            instruction: str,
    ) -> str:
        ...
