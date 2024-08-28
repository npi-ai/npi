from typing import List

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import create_model, Field

from npiai.context import Context, Task
from npiai.core.base import BaseAgentTool
from npiai.core.tool._browser import BrowserTool
from npiai.core.tool._function import FunctionTool
from npiai.types import FunctionRegistration
from npiai.utils import sanitize_schema


class AgentTool(BaseAgentTool):
    _tool: FunctionTool

    def __init__(self, tool: FunctionTool):
        super().__init__()
        self.name = f"{tool.name}_agent"
        self._tool = tool
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

    async def start(self):
        await self._tool.start()

    async def end(self):
        await self._tool.end()

    async def chat(
        self,
        ctx: Context,
        instruction: str,
    ) -> str:
        await ctx.setup_configs(instruction)

        task = Task(goal=instruction)
        ctx.with_task(task)
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

    async def _call_llm(self, ctx: Context, task: Task) -> str:
        while True:
            response = await ctx.llm.completion(
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

            results = await self._tool.call(tool_calls, ctx)
            await task.step(results)


class BrowserAgentTool(AgentTool):
    _tool: BrowserTool

    def __init__(self, tool: BrowserTool):
        super().__init__(tool)

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

        await ctx.setup_configs(instruction)

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
