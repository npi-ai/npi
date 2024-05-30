from typing import List, Dict, Any
from contextlib import asynccontextmanager

from openai.types.chat import ChatCompletionMessageToolCall, ChatCompletionToolMessageParam

from npiai.core import NPi


class AsyncNPi(NPi):
    async def call(self, tool_calls: List[ChatCompletionMessageToolCall]) -> List[ChatCompletionToolMessageParam]:
        return await self._call(tool_calls)

    async def chat(self, msg: str) -> str:
        return await self._chat(msg)

    async def debug(self, toolset: str = None, fn_name: str = None, args: Dict[str, Any] = None) -> str:
        return await self._debug(toolset, fn_name, args)

    async def start(self):
        await self._start()

    async def end(self):
        await self._end()

    @asynccontextmanager
    async def launch(self):
        try:
            await self._start()
            yield self
        finally:
            await self._end()
        
