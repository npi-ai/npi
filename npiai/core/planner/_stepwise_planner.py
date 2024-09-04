import json
from typing import List, Dict

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel, Field

from npiai.context import Context
from npiai.types import FunctionRegistration, ExecutionStep, Plan
from npiai.utils import llm_tool_call
from npiai.core.tool import AgentTool
from npiai.core.base import BaseTool

from ._base import BasePlanner


__PROMPT__ = """
Use the provided list of tools, develop a detailed plan to accomplish a specified task. 
The plan should consist of sequential steps where each step involves the use of a set of potential tools.
If a step requires initiating a chat with an AI Agent, it should exclusively feature that tool.
Ensure that the steps are presented in a clear and logical order. 
Conclude the plan by calling the `export` tool and include the final sequence of steps 
and the corresponding tools' name as its argument.

## Instructions for Planning

- Define the Goal: Clearly state the overall objective or purpose of the plan.
- Break Down the Task: Divide the goal into smaller, manageable steps that can be executed sequentially.
- Identify Tools: For each step, list the potential tools that can be used to accomplish the task.
- Sequence the Steps: Arrange the steps in a logical order that leads to the successful completion of the goal.

## Available Tools

{tools}

## Additional Rules

{rules}
"""


class StepResponse(BaseModel):
    task: str = Field(description="Specific task to be performed in this step")
    thought: str = Field(description="Detailed rationale or reasoning behind this step")
    potential_tools: List[str] = Field(
        description="List of potential tools (presented by their names) that can be used in this step"
    )


class PlanResponse(BaseModel):
    goal: str = Field(description="Overall goal for this plan")
    steps: List[StepResponse] = Field(description="A step-by-step execution plan")


class StepwisePlanner(BasePlanner):
    _fn_map: Dict[str, FunctionRegistration] = None

    @staticmethod
    def _get_tool_list(tool: BaseTool) -> str:
        tools = tool.tool.tools if isinstance(tool, AgentTool) else tool.tools
        return json.dumps(tools)

    def _build_fn_map(self, tool: BaseTool):
        functions = (
            tool.tool.unpack_functions()
            if isinstance(tool, AgentTool)
            else tool.unpack_functions()
        )

        if not self._fn_map:
            self._fn_map = {}

        for fn in functions:
            self._fn_map[fn.name] = fn

    async def generate_plan(
        self,
        ctx: Context,
        task: str,
        tool: BaseTool,
    ) -> Plan:
        self._build_fn_map(tool)

        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=__PROMPT__.format(
                    tools=self._get_tool_list(tool),
                    rules=self._rules,
                ),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=task,
            ),
        ]

        plan_response = await llm_tool_call(
            llm=ctx.llm,
            model=PlanResponse,
            tool=self.export,
            tool_description="generate a plan",
            messages=messages,
        )

        return await self.export(
            ctx=ctx,
            tool=tool,
            plan=plan_response,
        )

    async def export(self, ctx: Context, tool: BaseTool, plan: PlanResponse) -> Plan:
        steps = []

        for step in plan.steps:
            sub_plan = None
            agent = None

            for fn_name in step.potential_tools:
                if fn_name in self._fn_map and self._fn_map[fn_name].is_agent():
                    agent = self._fn_map[fn_name].calling_agent
                    break

            if agent:
                # init a new planner to generate sub plan
                sub_plan = await StepwisePlanner().generate_plan(
                    ctx=ctx,
                    task=step.task,
                    tool=agent,
                )

            steps.append(
                ExecutionStep(
                    task=step.task,
                    thought=step.thought,
                    potential_tools=[
                        self._fn_map[name]
                        for name in step.potential_tools
                        if name in self._fn_map
                    ],
                    sub_plan=sub_plan,
                )
            )

        return Plan(goal=plan.goal, steps=steps, toolset=tool)
