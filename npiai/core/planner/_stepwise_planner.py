import json
from typing import List, Dict

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel, Field

from npiai.context import Context
from npiai.types import FunctionRegistration, ExecutionStep, Plan
from npiai.utils import sanitize_schema
from npiai.core.tool import AgentTool, FunctionTool
from npiai.core.base import BaseTool

from ._base import BasePlanner


__PROMPT__ = """
Use the provided list of tools, develop a detailed plan to accomplish a specified task. 
The plan should consist of sequential steps where each step involves the use of a set of potential tools.
If a step requires initiating a chat with an AI Agent, it should exclusively feature that tool.
Ensure that the steps are presented in a clear and logical order. 
Conclude the plan by calling the `export` tool and include the final sequence of steps 
and the corresponding tools' name as its argument.

## Available Tools

Below is a list of tools, labeled with `tool_name: description`. 
Tools accompanied by `(Agent)` initiate a chat with an AI agent and are to be used independently within a step.
Note that you shouldn't call any tool in this list directly since they can only be included in the `potential_tools` list.
The only tool you can use is `export`.

{tools}

## Additional Rules

{rules}
"""


class StepResponse(BaseModel):
    task: str = Field(description="Detailed task of this step")
    potential_tools: List[str] = Field(
        description="A list of potential tools to invoke"
    )


class PlanResponse(BaseModel):
    goal: str = Field(description="Overall goal for this plan")
    steps: List[StepResponse] = Field(description="A step-by-step execution plan")


class StepwisePlanner(BasePlanner):
    _fn_map: Dict[str, FunctionRegistration]

    def _get_tool_list(self, tool: AgentTool | FunctionTool) -> str:
        tools = []
        self._fn_map = {}

        functions = (
            tool.tool.unpack_functions()
            if isinstance(tool, AgentTool)
            else tool.unpack_functions()
        )

        for fn in functions:
            agent_mark = "(Agent)" if fn.is_agent() else ""
            tools.append(f"- {fn.name}{agent_mark}: {fn.description}")
            self._fn_map[fn.name] = fn

        return "\n".join(tools)

    async def generate_plan(
        self,
        ctx: Context,
        task: str,
        tool: AgentTool | FunctionTool,
    ) -> Plan:
        fn_reg = FunctionRegistration(
            fn=self.export,
            name="export",
            description="Export generated plan",
            ctx_variables=[],
            model=PlanResponse,
            schema=sanitize_schema(PlanResponse),
        )
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
        response = await ctx.llm.completion(
            messages=messages,
            tools=[fn_reg.get_tool_param()],
            tool_choice="required",
            max_tokens=4096,
        )

        response_message = response.choices[0].message
        tool_calls = response_message.get("tool_calls", None)

        await ctx.send_debug_message(f"[StepwisePlanner] Received {tool_calls}]")

        if not tool_calls or tool_calls[0].function.name != "export":
            raise RuntimeError("No tool call received to devise an execution plan")

        args = json.loads(tool_calls[0].function.arguments)

        return await self.export(
            ctx=ctx,
            tool=tool,
            plan=PlanResponse(**args),
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
                sub_plan = await self.generate_plan(
                    ctx=ctx,
                    task=step.task,
                    tool=agent,
                )

            steps.append(
                ExecutionStep(
                    task=step.task,
                    fn_candidates=[
                        self._fn_map[name]
                        for name in step.potential_tools
                        if name in self._fn_map
                    ],
                    sub_plan=sub_plan,
                )
            )

        return Plan(goal=plan.goal, steps=steps, tool=tool)
