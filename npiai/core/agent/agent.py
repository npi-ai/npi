import os
import asyncio
import signal
import sys
from abc import ABC
from typing import List, overload

from litellm.types.completion import ChatCompletionMessageParam
from fastapi import FastAPI, Request

import uvicorn
from npiai.llm import LLM, OpenAI
from npiai.utils import logger
from npiai.types import FunctionRegistration
from npiai.core.app import App
from npiai.core.app.browser import BrowserApp
from npiai.core.base import BaseAgent
from npiai.core.hitl import HITL
from npiai.core.thread import Thread, ThreadMessage
from npiai.core import callback


class Agent(BaseAgent):
    _app: App

    def __init__(self, app: App, llm: LLM = None):
        super().__init__()
        self._app = app
        self.llm = llm or OpenAI(api_key=os.environ.get('OPENAI_API_KEY', None), model='gpt-4o')
        self.name = f'{app.name}__agent'
        self.description = app.description
        self.provider = app.provider

    def unpack_functions(self) -> List[FunctionRegistration]:
        # Wrap the chat function of this agent to FunctionRegistration
        fn_reg = FunctionRegistration(
            fn=self.chat,
            name='chat',
            description=self._app.description,
            schema={
                'type': 'object',
                'properties': {
                    'message': {
                        'type': 'string',
                        'description': f'The task you want {self._app.name} to do or the message you want to chat with {self._app.name}'
                    },
                },
                'required': ['message'],
            }
        )

        return [fn_reg]

    def use_hitl(self, hitl: HITL):
        super().use_hitl(hitl)
        self._app.use_hitl(hitl)

    async def start(self):
        await self._app.start()

    async def end(self):
        await self._app.end()

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
            thread: Thread = None,
    ) -> str:
        if thread is None:
            thread = Thread('')

        msg = thread.fork(message)
        if self._app.system_prompt:
            msg.append(
                {
                    'role': 'system',
                    'content': self._app.system_prompt,
                }
            )

        msg.append(
            {
                'role': 'user',
                'content': message,
            }
        )

        return await self._call_llm(thread, msg)

    async def _call_llm(self, thread: Thread, message: ThreadMessage) -> str:
        while True:
            response = await self.llm.completion(
                messages=message.raw(),
                tools=self._app.tools,
                tool_choice='auto',
                max_tokens=4096,
            )

            response_message = response.choices[0].message

            message.append(response_message)

            if response_message.content:
                logger.info(response_message.content)
                await thread.send_msg(callback.Callable(response_message.content))

            tool_calls = response_message.get('tool_calls', None)

            if tool_calls is None:
                return response_message.content

            results = await self._app.call(tool_calls)
            message.extend(results)


class BrowserAgent(Agent):
    _app: BrowserApp

    def __init__(self, app: BrowserApp, llm: LLM = None):
        super().__init__(app, llm)

    async def chat(
            self,
            message: str,
            thread: Thread = None,
    ) -> str:
        if not self._app.use_screenshot:
            return await super().chat(message)

        screenshot = await self._app.get_screenshot()

        if not screenshot:
            return await super().chat(message)

        messages: List[ChatCompletionMessageParam] = []

        if self._app.system_prompt:
            messages.append(
                {
                    'role': 'system',
                    'content': self._app.system_prompt,
                }
            )

        messages.append(
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

        return await self._call_llm(messages)


@overload
def agent_wrapper(app: App, llm: LLM = None) -> Agent:
    ...


@overload
def agent_wrapper(app: BrowserApp, llm: LLM = None) -> BrowserAgent:
    ...


def agent_wrapper(app: App | BrowserApp, llm: LLM = None) -> Agent | BrowserAgent:
    if isinstance(app, App):
        return Agent(app, llm)

    if isinstance(app, BrowserApp):
        return BrowserAgent(app, llm)

    raise TypeError(f'app must be an instance of App or BrowserApp')
