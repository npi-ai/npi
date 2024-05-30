from typing import List, Dict, Any
from contextlib import contextmanager
import asyncio

from openai.types.chat import ChatCompletionMessageToolCall, ChatCompletionToolMessageParam

from npiai.core import NPi


class SyncNPi(NPi):
    def call(self, tool_calls: List[ChatCompletionMessageToolCall]) -> List[ChatCompletionToolMessageParam]:
        return asyncio.run(self._call(tool_calls))

    def chat(self, msg: str) -> str:
        return asyncio.run(self._chat(msg))

    def debug(self, toolset: str = None, fn_name: str = None, args: Dict[str, Any] = None) -> str:
        return asyncio.run(self._debug(toolset, fn_name, args))

    def start(self):
        return asyncio.run(self._start())

    def end(self):
        return asyncio.run(self._end())

    @contextmanager
    def launch(self):
        try:
            self.start()
            yield self
        finally:
            self.end()
