import os
from typing import List

from litellm.types.completion import ChatCompletionMessageParam

from npiai.llm import LLM, OpenAI
from npiai.utils import logger
from npiai.types import FunctionRegistration
from npiai.core.base import BaseAgent
from .app import App


class Agent(BaseAgent):
    _app: App

    def __init__(self, app: App, llm: LLM = None):
        super().__init__()
        self._app = app
        self.llm = llm or OpenAI(api_key=os.environ.get('OPENAI_API_KEY', None), model='gpt-4o')
        self.name = app.name
        self.description = app.description

    def list_functions(self) -> List[FunctionRegistration]:
        # Wrap the chat function of this agent to FunctionRegistration

        async def tool_chat(task: str) -> str:
            return await self.chat(task)

        fn_reg = FunctionRegistration(
            fn=tool_chat,
            name=self._app.name,
            description=self._app.description,
            schema={
                'type': 'object',
                'properties': {
                    'task': {
                        'type': 'string',
                        'description': f'The task you want {self._app.name} to do'
                    },
                },
                'required': ['task'],
            }
        )

        return [fn_reg]

    async def start(self):
        await self._app.start()

    async def end(self):
        await self._app.end()

    async def chat(
        self,
        message: str,
    ) -> str:
        messages: List[ChatCompletionMessageParam] = []

        if self._app.system_role:
            messages.append(
                {
                    'role': 'system',
                    'content': self._app.system_role,
                }
            )

        messages.append(
            {
                'role': 'user',
                'content': message,
            }
        )

        return await self._call_llm(messages)

    async def _call_llm(self, messages: List[ChatCompletionMessageParam]) -> str:
        while True:
            response = await self.llm.completion(
                messages=messages,
                tools=self._app.tools,
                tool_choice='auto',
                max_tokens=4096,
            )

            response_message = response.choices[0].message

            messages.append(response_message)

            if response_message.content:
                logger.info(response_message.content)

            tool_calls = response_message.get('tool_calls', None)

            if tool_calls is None:
                return response_message.content

            results = await self._app.call(tool_calls)
            messages.extend(results)
