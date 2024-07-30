import os
from typing import List

from pydantic import create_model, Field

from npiai.llm import LLM, OpenAI
from npiai.types import FunctionRegistration
from npiai.context import Context, Task
from npiai.core.base import BaseAgentTool
from npiai.core.hitl import HITL
from npiai.core.tool._function import FunctionTool
from npiai.core.tool._browser import BrowserTool
from npiai.utils import sanitize_schema

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)


class AgentTool(BaseAgentTool):
    llm: LLM
    _tool: FunctionTool

    def __init__(self, tool: FunctionTool, llm: LLM = None):
        super().__init__()
        self.name = f"{tool.name}_agent"
        self._tool = tool
        self.llm = llm or OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", None), model="gpt-4o"
        )
        self.description = tool.description
        self.provider = tool.provider

    def unpack_functions(self) -> List[FunctionRegistration]:
        # Wrap the chat function of this agent to FunctionRegistration
        model = create_model(
            f"{self.name}_agent_model",
            instruction=(
                str,
                Field(
                    description=f"The task you want {self._tool.name} to do or "
                    f"the message you want to chat with {self._tool.name}"
                ),
            ),
        )

        fn_reg = FunctionRegistration(
            fn=self.chat,
            name="chat",
            ctx_variables=[],
            ctx_param_name="ctx",
            description=f"This is an api of an AI Assistant, named {self.name}, the abilities of the assistant is:\n "
            f"{self.description}\n"
            f"You can use this function to direct the assistant to accomplish task for you.",
            model=model,
            schema=sanitize_schema(model),
        )

        return [fn_reg]

    def use_hitl(self, hitl: HITL):
        super().use_hitl(hitl)
        self._tool.use_hitl(hitl)

    async def start(self):
        await self._tool.start()

    async def end(self):
        await self._tool.end()

    async def chat(
        self,
        ctx: Context,
        instruction: str,
    ) -> str:
        task = Task(goal=instruction)
        ctx = ctx.fork(task)
        if self._tool.system_prompt:
            await task.step(
                [
                    ChatCompletionSystemMessageParam(
                        role="system", content=self._tool.system_prompt
                    )
                ]
            )

        await task.step(
            [ChatCompletionUserMessageParam(role="user", content=instruction)]
        )
        return await self._call_llm(ctx, task)

    async def _call_llm(self, session: Context, task: Task) -> str:
        while True:
            response = await self.llm.completion(
                messages=task.conversations(),
                tools=self._tool.tools,
                tool_choice="auto",
                max_tokens=4096,
            )
            await task.step([response.choices[0].message])

            response_message = response.choices[0].message
            tool_calls = response_message.get("tool_calls", None)

            if tool_calls is None:
                return response_message.content

            results = await self._tool.call(tool_calls, session)
            await task.step(results)


class BrowserAgentTool(AgentTool):
    _tool: BrowserTool

    def __init__(self, tool: BrowserTool, llm: LLM = None):
        super().__init__(tool, llm)

    async def get_screenshot(self) -> str | None:
        return await self._tool.get_screenshot()

    async def goto_blank(self):
        await self._tool.goto_blank()

    async def chat(
        self,
        ctx: Context,
        instruction: str,
    ) -> str:
        if not self._tool.use_screenshot:
            return await super().chat(ctx, instruction)

        screenshot = await self._tool.get_screenshot()

        if not screenshot:
            return await super().chat(ctx, instruction)

        task = Task(goal=instruction)
        ctx = ctx.fork(task)
        if self._tool.system_prompt:
            await task.step(
                [
                    ChatCompletionSystemMessageParam(
                        role="system", content=self._tool.system_prompt
                    )
                ]
            )

        await task.step(
            [
                ChatCompletionUserMessageParam(
                    role="user",
                    content=[
                        {
                            "type": "text",
                            "text": instruction,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": screenshot,
                            },
                        },
                    ],
                )
            ]
        )

        return await self._call_llm(ctx, task)
