from typing import List
from textwrap import dedent

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import create_model, Field

from npiai.context import Context, Task
from npiai.core.base import BaseAgentTool
from npiai.types import FunctionRegistration, Plan
from npiai.utils import sanitize_schema

from ._browser import BrowserTool
from ._function import FunctionTool


class AgentTool(BaseAgentTool):
    _tool: FunctionTool

    @property
    def tool(self) -> FunctionTool:
        return self._tool

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
                    description=dedent(
                        f"""
                        The task you want {self._tool.name} to do or the message you want to chat with {self._tool.name}.
                        Provide as many details as you can.
                        """
                    )
                ),
            ),
        )

        fn_reg = FunctionRegistration(
            fn=self.chat,
            calling_agent=self,
            name="chat",
            ctx_variables=[],
            ctx_param_name="ctx",
            model=model,
            schema=sanitize_schema(model),
            description=dedent(
                f"""
                Initiate a conversation with an AI Agent named "{self.name}".
                This agent has the following abilities: {self.description}.
                Describe a scenario or pose a question to engage its assistance effectively.
                You must provide as many details as you can since this agent can't access the chat history.
                """
            ),
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
            await task.step([await self._generate_system_message()])

        await task.step([await self._generate_user_message(instruction)])
        final_result = await self._call_llm(ctx, task)

        return final_result

    async def execute_plan(
        self,
        ctx: Context,
        plan: Plan,
    ) -> str:
        """
        Execute a pre-generated stepwise plan.

        Args:
            ctx: NPi Context
            plan: Pre-generated plan

        Returns:
            Final result
        """
        result = ""

        for step in plan.steps:
            if step.sub_plan and isinstance(step.sub_plan.toolset, AgentTool):
                await step.sub_plan.toolset.execute_plan(ctx, step.sub_plan)
            else:
                await ctx.send_debug_message(
                    f"[{self.name}] Performing task: {step.task}"
                )

                instruction = dedent(
                    f"""
                    Analyze the chat history and develop a strategy to successfully execute the task described below. 
                    Use the lessons learned from the past results to shape your strategy for this new task.
                    Review the previous actions and adjust the task to fit the goal if necessary.
                    You should stop further generation as soon as the new task is complete.
                    
                    ## New Task to Complete
                    Task: {step.task}
                    Reasoning behind the task: {step.thought}
                    
                    ## Preferred Tools
                    In formulating your strategy, give preference to the following tools:
                    {[fn.name for fn in step.potential_tools]}
                    """
                )

                await ctx.send_debug_message(f"Instruction:\n{instruction}")

                result = await self.chat(ctx, instruction)

                await ctx.send_debug_message(f"[{self.name}] Result: {result}")

        return result

    async def _generate_system_message(self) -> ChatCompletionSystemMessageParam:
        return ChatCompletionSystemMessageParam(
            role="system",
            content=self._tool.system_prompt,
        )

    async def _generate_user_message(
        self,
        instruction: str,
    ) -> ChatCompletionUserMessageParam:
        return ChatCompletionUserMessageParam(
            role="user",
            content=instruction,
        )

    async def _call_llm(self, ctx: Context, task: Task) -> str:
        system_msgs = [msg for msg in task.conversations() if msg["role"] == "system"]

        while True:
            messages = [*system_msgs, *ctx.get_history_messages(exclude_system=True)]

            response = await ctx.llm.completion(
                messages=messages,
                # messages=task.conversations(),
                tools=self._tool.tools,
                tool_choice="auto",
                max_tokens=4096,
            )

            response_message = response.choices[0].message
            tool_calls = response_message.get("tool_calls", None)

            if tool_calls is None:
                await task.step([response_message])
                return response_message.content

            results = await self._tool.call(tool_calls, ctx)
            await task.step([response_message])
            await task.step(results)


class BrowserAgentTool(AgentTool):
    _tool: BrowserTool

    def __init__(self, tool: BrowserTool):
        super().__init__(tool)

    async def get_screenshot(self) -> str | None:
        return await self._tool.get_screenshot()

    async def goto_blank(self):
        await self._tool.goto_blank()

    async def _generate_user_message(
        self,
        instruction: str,
    ) -> ChatCompletionUserMessageParam:
        screenshot = await self._tool.get_screenshot()

        if not screenshot:
            return await super()._generate_user_message(instruction)

        return ChatCompletionUserMessageParam(
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
