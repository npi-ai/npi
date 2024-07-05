import os
import asyncio
import signal
import sys
from typing import List, overload

from litellm.types.completion import ChatCompletionMessageParam
from fastapi import FastAPI, Request

import uvicorn
from npiai.llm import LLM, OpenAI
from npiai.utils import logger
from npiai.types import FunctionRegistration
from npiai.context import Context, ThreadMessage
from npiai.core import callback
from npiai.core.base import BaseAgentTool
from npiai.core.hitl import HITL
from npiai.core.tool.function import FunctionTool
from npiai.core.tool.browser import BrowserTool


class AgentTool(BaseAgentTool):

    def __init__(self, tool: FunctionTool, llm: LLM = None):
        self.name = f'{tool.name}_agent'
        self._tool = tool
        self.llm = llm or OpenAI(api_key=os.environ.get('OPENAI_API_KEY', None), model='gpt-4o')
        self.description = tool.description
        self.provider = tool.provider
        super().__init__(tool.name, tool.description, tool.provider)

    def unpack_functions(self) -> List[FunctionRegistration]:
        # Wrap the chat function of this agent to FunctionRegistration

        def chat(message: str, ctx: Context):
            # TODO: pass thread down
            return self.chat(message, ctx)

        fn_reg = FunctionRegistration(
            fn=chat,
            name='chat',
            ctx_param_name='ctx',
            description=self._tool.description,
            schema={
                'type': 'object',
                'properties': {
                    'message': {
                        'type': 'string',
                        'description': f'The task you want {self._tool.name} to do or the message you want to chat with {self._tool.name}'
                    },
                },
                'required': ['message'],
            }
        )

        return [fn_reg]

    def use_hitl(self, hitl: HITL):
        # super().use_hitl(hitl)
        self._tool.use_hitl(hitl)

    async def start(self):
        await self._tool.start()

    async def end(self):
        await self._tool.end()

    async def server(self):
        """Start the server"""
        await self.start()
        if not bool(os.environ.get("NPIAI_TOOL_SERVER_MODE")):
            return

        fapp = FastAPI()

        @fapp.api_route("/chat", methods=["POST"])
        async def root(request: Request):
            args = await request.json()
            return self.chat(args['message'])

        def signal_handler(sig, frame):
            print(f"Signal {sig} received, shutting down.")
            asyncio.create_task(self.end())
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        uvicorn.run(fapp, host="0.0.0.0", port=18000)

    async def chat(
            self,
            message: str,
            thread: Context = None,
    ) -> str:
        if thread is None:
            thread = Context('')

        msg = thread.fork(message)
        if self._tool.system_prompt:
            msg.append(
                {
                    'role': 'system',
                    'content': self._tool.system_prompt,
                }
            )

        msg.append(
            {
                'role': 'user',
                'content': message,
            }
        )

        return await self._call_llm(thread, msg)

    async def _call_llm(self, thread: Context, message: ThreadMessage) -> str:
        while True:
            response = await self.llm.completion(
                messages=message.raw(),
                tools=self._tool.tools,
                tool_choice='auto',
                max_tokens=4096,
            )

            response_message = response.choices[0].message

            message.append(response_message)

            if response_message.content:
                # logger.info(response_message.content)
                await thread.send_msg(callback.Callable(response_message.content))

            tool_calls = response_message.get('tool_calls', None)

            if tool_calls is None:
                return response_message.content

            results = await self._tool.call(tool_calls, thread)
            message.extend(results)


class BrowserAgentTool(AgentTool):

    def __init__(self, tool: BrowserTool, llm: LLM = None):
        self._tool = tool
        super().__init__(tool, llm)

    async def get_screenshot(self) -> str | None:
        return await self._tool.get_screenshot()

    async def goto_blank(self):
        await self._tool.goto_blank()

    async def chat(
            self,
            message: str,
            ctx: Context = None,
    ) -> str:
        if ctx is None:
            ctx = Context('')

        if not self._tool.use_screenshot:
            return await super().chat(message, ctx)

        screenshot = await self._tool.get_screenshot()

        if not screenshot:
            return await super().chat(message, ctx)

        msg = ctx.fork(message)
        if self._tool.system_prompt:
            msg.append(
                {
                    'role': 'system',
                    'content': self._tool.system_prompt,
                }
            )

        msg.append(
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': message,
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': screenshot,
                        },
                    },
                ]
            }
        )

        return await self._call_llm(ctx, msg)


@overload
def agent_wrapper(tool: FunctionTool, llm: LLM = None) -> AgentTool:
    ...


@overload
def agent_wrapper(tool: BrowserTool, llm: LLM = None) -> BrowserAgentTool:
    ...


def agent_wrapper(tool: FunctionTool | BrowserTool, llm: LLM = None) -> AgentTool | BrowserAgentTool:
    if isinstance(tool, BrowserTool):
        return BrowserAgentTool(tool, llm)

    if isinstance(tool, FunctionTool):
        return AgentTool(tool, llm)

    raise TypeError(f'app must be an instance of FunctionTool or BrowserTool')
