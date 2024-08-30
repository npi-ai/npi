import json
from typing import List
from textwrap import dedent
from dataclasses import asdict

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import create_model, Field

from npiai.context import Context, Task
from npiai.core.base import BaseAgentTool
from npiai.types import FunctionRegistration, Plan, ExecutionResult
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
                        The task you want {self._tool.name} to do or 
                        the message you want to chat with {self._tool.name}
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
        # TODO: use history from context
        history: List[ExecutionResult] = None,
    ) -> str:
        """
        Execute a pre-generated stepwise plan.

        Args:
            ctx: NPi Context
            plan: Pre-generated plan
            history: Execution history

        Returns:
            Final result
        """
        if history is None:
            history = []

        for step in plan.steps:
            if step.sub_plan and isinstance(step.sub_plan.tool, AgentTool):
                await step.sub_plan.tool.execute_plan(ctx, step.sub_plan, history)
            else:
                previous_results = [asdict(hist) for hist in history]

                await self.chat(
                    ctx=ctx,
                    instruction=dedent(
                        f"""
                        Analyze the provided JSON data of previous outcomes and develop a strategy to 
                        successfully execute the task described below. 
                        Use the lessons learned from the past results to shape your strategy for this new task.
                        
                        ## JSON Data of Past Outcomes
                        {json.dumps(previous_results, ensure_ascii=False)}
                        
                        ## New Task to Complete
                        {step.task}
                        """
                    ),
                )

        return history[-1].result if len(history) else "No result"

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
