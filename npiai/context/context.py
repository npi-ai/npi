"""This module contains the classes for the context and context message"""

import datetime
import json
import uuid
import asyncio
from typing import List, Union, Dict, TYPE_CHECKING, TypeVar, Type, Any
from textwrap import dedent

from mem0 import Memory
from litellm.types.completion import ChatCompletionMessageParam
from pydantic import create_model, Field

from npiai.utils import sanitize_schema, logger

if TYPE_CHECKING:
    from npiai.core import BaseTool


_T = TypeVar("_T")


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

    _q: asyncio.Queue
    _is_finished: bool
    _is_failed: bool
    _result: str
    _failed_msg: str
    _last_screenshot: str | None
    _active_tool: Union["BaseTool", None]
    _memory: Memory
    _query_cache: Dict[str, Any]

    def __init__(
        self,
        memory: Memory = Memory(),
    ) -> None:
        self.id = str(uuid.uuid4())
        self._q = asyncio.Queue()
        self._is_finished = False
        self._result = ""
        self._is_failed = False
        self._failed_msg = ""
        self._last_screenshot = None
        self._active_tool = None
        self._memory = memory
        self._query_cache = {}

    async def _ask_human(self, query: str):
        """
        Ask human if no memory is found

        Args:
            query: Memory search query
        """
        if not self._active_tool:
            raise RuntimeError("No active tool found")

        res = await self._active_tool.hitl.input(
            ctx=self,
            tool_name=self._active_tool.name,
            message=f"Please provide the following information: {query}",
        )

        await self.save(f"Question: {query}? Answer: {res}")

    async def save(self, info: str):
        """
        Save the given information into memory

        Args:
            info: Information to save
        """
        m = self._memory.add(
            data=info,
            run_id=self.id,
            metadata={"raw": info},
            prompt=dedent(
                f"""
                Deduce the facts, preferences, and memories from the provided text.
                Just return the facts, preferences, and memories in bullet points:
                Natural language text: {info}
                
                Constraint for deducing facts, preferences, and memories:
                - The facts, preferences, and memories should be concise and informative.
                - Don't start by "The person likes Pizza". Instead, start with "Likes Pizza".
                - Don't remember the user/agent details provided. Only remember the facts, preferences, and memories.
                
                Deduced facts, preferences, and memories:
                """
            ),
        )
        # clear cache
        self._query_cache = {}
        logger.debug(f"Saved memory: {m}")

    async def ask(
        self,
        query: str,
        return_type: Type[_T] = str,
        constraints: str = None,
        _is_retry: bool = False,
    ) -> _T:
        """
        Search the memory

        Args:
            query: Memory search query
            return_type: Return type of the result
            constraints: Search constraints
            _is_retry: Retry flag
        """
        cached_result = self._query_cache.get(query, None)

        if cached_result:
            return cached_result

        async def retry():
            if _is_retry:
                return

            # invoke HITL and retry
            await self._ask_human(query)
            return await self.ask(query, return_type, constraints, _is_retry=True)

        memories = self._memory.search(query, run_id=self.id, limit=10)
        logger.debug(f"Retrieved memories: {json.dumps(memories)}")

        if len(memories) == 0:
            logger.info(f"No memories found for query: {query}")
            return await retry()

        mem_str = "- " + "\n- ".join(
            "Extracted data: " + m["text"] + "\n Raw data: " + m["metadata"]["raw"]
            for m in memories
        )

        callback_model = create_model(
            "MemorySearchCallback",
            data=(
                return_type,
                Field(
                    default=None,
                    description="Retrieved memories. Set to `null` if no data is found.",
                ),
            ),
        )

        schema = sanitize_schema(callback_model)

        # TODO: use npi llm client?
        response = self._memory.llm.generate_response(
            tool_choice="required",
            messages=[
                {
                    "role": "system",
                    "content": dedent(
                        f"""
                        Optimize the functioning of a memory retrieval AI tool by adhering to the following guidelines for processing search queries:

                        1. Respond to search queries by invoking the `callback` function, supplying the required information within the `data` argument.
                        2. When delivering the `data`, aim for brevity and accuracy—only include the core details pertinent to the query.
                           - For instance, rather than "The capital of France is Paris," provide the succinct "Paris."
                        3. Ensure the content in `data` is an exact match to the search query.
                           - As an example, "The password for the Wi-Fi is '1234Abcd'" should only be returned if the query is "Wi-Fi password" and not for "macOS password" or any other password-related question.
                        4. Adhere to any specified constraints in the retrieval process.

                        ## Memories
                        """
                    )
                    + mem_str,
                },
                {
                    "role": "user",
                    "content": dedent(
                        f"""
                        Query: {query}
                        Constraints: {constraints}
                        """
                    ),
                },
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "callback",
                        "description": "Callback with retrieved information from the given memory",
                        "parameters": schema,
                    },
                }
            ],
        )

        tool_calls = response["tool_calls"]

        if not tool_calls or tool_calls[0]["name"] != "callback":
            logger.info(
                f"No LLM callback found for query: {query}. Response: {json.dumps(response)}"
            )
            return await retry()

        logger.debug(f"LLM callback: {json.dumps(tool_calls)}")

        data = tool_calls[0]["arguments"].get("data", None)

        if data is None:
            logger.info(f"No data found for query: {query}")
            return await retry()

        self._query_cache[query] = data

        return data

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

    async def refresh_screenshot(self) -> str | None:
        """
        Refresh and return the latest screenshot of the running tools.

        Returns:
            None if no screenshot is available or the screenshot stays unchanged.
            Otherwise, return the latest screenshot.
        """
        if not self._active_tool or self.is_finished():
            return None

        screenshot = await self._active_tool.get_screenshot()

        if screenshot == self._last_screenshot:
            return None

        self._last_screenshot = screenshot

        return screenshot

    async def send(self, cb: str) -> None:
        """send a message to the context"""
        # self.cb_dict[cb.id()] = cb
        await self._q.put(cb)

    async def fetch(self):
        """receive a message"""
        while not self.is_failed() and not self.is_finished():
            try:
                item = self._q.get_nowait()
                if item:
                    return item
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.01)

    def get_callback(self, cb_id: str):
        pass
        # return self.cb_dict[cb_id]

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
