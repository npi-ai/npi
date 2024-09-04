import json
from textwrap import dedent
from typing import Dict, List, Optional, TYPE_CHECKING

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel, Field

from npiai.types import Plan, ExecutionStep, FunctionRegistration
from npiai.context import Context
from npiai.core.tool import AgentTool
from npiai.utils import llm_tool_call

from ._base import BaseOptimizer

if TYPE_CHECKING:
    from npiai.core import BaseTool


# TODO: include tools in the prompt?
__PROMPT__ = """
Review the given execution plan and identify any potential steps that can be combined or eliminated.
Propose an optimized plan that eliminates unnecessary tasks, consolidates similar actions, 
and ensures a clear, concise, and logical flow from beginning to end.

## Instructions for Optimization

- Eliminate Redundancies: Look for any tasks that are duplicated or serve the same purpose. Remove or merge these tasks to prevent repetitive actions.
- Streamline the Workflow: Arrange the tasks in a logical sequence that reflects the natural process. Each task must contribute directly to achieving the goal.
- Enhance Efficiency: Consider the dependencies between tasks. Adjust the order or grouping of tasks to minimize delays in the plan's execution.
- Keep Hierarchy: Ensure that the optimized plan maintains the hierarchical structure of the original plan, including sub-plans and nested steps.
- Avoid Unnecessary Combining: While consolidation is encouraged, avoid merging tasks that are distinct or require separate considerations.
- Avoid Over-Optimization: Focus on improving the plan's clarity and efficiency without sacrificing essential steps or details.

## Input Data Structure

The execution plan consists of the following components:

type Plan = {{
    goal: string, // The overall objective or purpose of the plan
    steps: ExecutionStep[], // A list of individual steps to be executed
    toolset: string, // Name of the toolset associated with the plan
}}

type ExecutionStep = {{
    id: string, // Unique identifier for this step
    task: string, // The specific task to be performed in this step
    thought: string, // The rationale or reasoning behind this task
    potential_tools: string[], // List of potential tools that can be used in this step
    sub_plan: Plan, // Sub-plan associated with this step (if applicable)
}}

## Additional Rules

{rules}
"""


class OptimizationStepResponse(BaseModel):
    id: str = Field(
        description="Unique identifier for this step. Obtained from the original plan"
    )
    task: str = Field(description="Specific task to be performed in this step")
    thought: str = Field(description="Detailed rationale or reasoning behind this step")
    potential_tools: List[str] = Field(
        description="A list of potential tools to invoke"
    )
    sub_plan: Optional["OptimizationPlanResponse"] = Field(
        description="Sub-plan associated with this step (if applicable)"
    )


class OptimizationPlanResponse(BaseModel):
    goal: str = Field(description="Overall goal for the optimized plan")
    toolset: str = Field(
        description="Name of the toolset associated with the optimized plan"
    )
    steps: List[OptimizationStepResponse] = Field(
        description="A step-by-step optimized plan"
    )


class DedupOptimizer(BaseOptimizer):
    _toolsets: Dict[str, "BaseTool"]

    def _build_toolsets(self, plan: Plan):
        self._toolsets = {}

        def build(p: Plan):
            self._toolsets[p.toolset.name] = p.toolset
            for step in p.steps:
                if step.sub_plan:
                    build(step.sub_plan)

        build(plan)

    def _get_tool_list(self) -> str:
        results = []

        for tool_name, tool in self._toolsets.items():
            tools = tool.tool.tools if isinstance(tool, AgentTool) else tool.tools
            results.append(
                dedent(
                    f"""
                    Toolset: {tool_name}
                    Tools: {json.dumps(tools, ensure_ascii=False)}
                    """
                )
            )

        return "\n".join(results)

    async def optimize(self, ctx: Context, plan: Plan) -> Plan:
        self._build_toolsets(plan)

        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=__PROMPT__.format(
                    # tools=self._get_tool_list(),
                    rules=self._rules,
                ),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=dedent(
                    f"""
                    The execution plan to be optimized is as follows:
                    {json.dumps(plan.to_json_object(), ensure_ascii=False)}
                    """
                ),
            ),
        ]

        plan_response = await llm_tool_call(
            llm=ctx.llm,
            model=OptimizationPlanResponse,
            tool=self.export,
            tool_description="Export optimized plan",
            messages=messages,
        )

        return await self.export(plan_response=plan_response)

    async def export(self, plan_response: OptimizationPlanResponse) -> Plan:
        steps: List[ExecutionStep] = []
        toolset = self._toolsets[plan_response.toolset]
        functions = (
            toolset.tool.unpack_functions()
            if isinstance(toolset, AgentTool)
            else toolset.unpack_functions()
        )
        toolset_fn_map = {fn.name: fn for fn in functions}

        for step in plan_response.steps:
            sub_plan = None
            if step.sub_plan:
                sub_plan = await self.export(step.sub_plan)

            potential_tools: List[FunctionRegistration] = []

            for tool_name in step.potential_tools:
                if tool_name in toolset_fn_map:
                    potential_tools.append(toolset_fn_map[tool_name])

            steps.append(
                ExecutionStep(
                    id=step.id,
                    task=step.task,
                    thought=step.thought,
                    potential_tools=potential_tools,
                    sub_plan=sub_plan,
                )
            )

        return Plan(
            goal=plan_response.goal,
            steps=steps,
            toolset=self._toolsets[plan_response.toolset],
        )
