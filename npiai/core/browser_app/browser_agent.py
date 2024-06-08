from typing import List

from litellm.types.completion import ChatCompletionMessageParam

from npiai import LLM
from npiai.core import Agent
from npiai.core.browser_app.browser_app import BrowserApp


class BrowserAgent(Agent):
    _app: BrowserApp

    def __init__(self, app: BrowserApp, llm: LLM = None):
        super().__init__(app, llm)

    async def chat(
        self,
        message: str
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
