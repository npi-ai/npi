import json
import re
from textwrap import dedent
from typing import Dict, List, Literal

from litellm.types.completion import ChatCompletionUserMessageParam
from pydantic import BaseModel

from npiai.context import Context
from npiai.types import FunctionRegistration, ExecutionStep, Plan
from npiai.core.tool import AgentTool
from npiai.core.base import BaseTool
from npiai.llm import OpenAI

from .base import BasePlanner


__PROMPT__ = """
Use the provided list of tools, develop a detailed plan to accomplish a specified task. 
The plan should consist of sequential steps where each step involves the use of a set of potential tools.
If a step requires initiating a chat with an AI Agent, it should exclusively feature that tool.
Ensure that the steps are presented in a clear and logical order.

## Instructions for Planning

- **Define the Goal**: Clearly state the overall objective or purpose of the plan.
- **Explore the Configs**: Understand the existing configurations and rules that apply to the task. Note that the context is visible to all tasks, so avoid asking for redundant information.
- **Review the Rules**: Familiarize yourself with the additional rules that may impact the task.
- **Break Down the Task**: Divide the goal into smaller, manageable steps that can be executed sequentially.
- **Identify Tools**: For each step, list the potential tools that can be used to accomplish the task.
- **Provide Rationale**: Explain the reasoning behind each step and why it is necessary to achieve the goal.
- **Sequence the Steps**: Arrange the steps in a logical order that leads to the successful completion of the goal.
- **Single Call of Agents**: If a step requires initiating a chat with an AI Agent, i.e., calling a tool with the postfix "_agent_chat", ensure that it is the only tool used in that step.

## Response Format

Return a JSON object with the following structure:

```json
{
  "goal": "string",
  "steps": [
    {
      "task": "string",
      "thought": "string",
      "potential_tools": ["string"]
    }
  ]
}
```

**Explanation of the fields**:
- `goal`: Overall goal for the plan
- `steps`: A list of steps to be performed in the plan, each containing:
    * `task`: Specific task to be performed in this step
    * `thought`: Detailed rationale or reasoning behind this step
    * `potential_tools`: List of potential tools (presented by their names) that can be used in this step
    
The response should be in the above format, with the appropriate values filled in for each field.

## Example

**Task**: Book a flight ticket from New York to Los Angeles.
**Tools**: [flight_search, payment_gateway, ticket_booking, ...]
**Configs**: { "first_name": "Alice", "last_name": "Smith", "email": "...", ... }
**Additional Rules**: [Rule 1, Rule 2, Rule 3, ...]
**Response**: {
    "goal": "Book a flight ticket from New York to Los Angeles",
    "steps": [
        {
            "task": "Search for available flights from New York to Los Angeles",
            "thought": "Find the best flight options based on price, timing, and other preferences",
            "potential_tools": ["flight_search"]
        },
        {
            "task": "Select a suitable flight and proceed to booking",
            "thought": "Choose the flight that meets the requirements and proceed with the booking process",
            "potential_tools": ["ticket_booking", "payment_gateway"]
        },
        ...
    ]
}
"""


class StepResponse(BaseModel):
    task: str
    thought: str
    potential_tools: List[str]


class PlanResponse(BaseModel):
    goal: str
    steps: List[StepResponse]


class ExperimentalO1Planner(BasePlanner):
    _fn_map: Dict[str, FunctionRegistration] = None
    _openai_api_key: str
    _openai: OpenAI

    def __init__(
        self,
        openai_api_key: str,
        o1_model: Literal["o1-preview", "o1-mini"] = "o1-preview",
        rules: str | None = None,
    ):
        super().__init__(rules)
        self._openai_api_key = openai_api_key
        self._openai = OpenAI(model=o1_model, api_key=openai_api_key)

    @staticmethod
    def _get_tool_list(tool: BaseTool) -> str:
        tools = tool.tool.tools if isinstance(tool, AgentTool) else tool.tools
        return json.dumps(tools)

    @staticmethod
    def _parse_response(response: str) -> PlanResponse | None:
        try:
            match = re.match(r"```.*\n([\s\S]+)```", response)
            data = json.loads(match.group(1)) if match else json.loads(response)
            return PlanResponse(**data)
        except json.JSONDecodeError:
            return None

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
            ChatCompletionUserMessageParam(
                role="user",
                content=dedent(
                    f"""
                    {__PROMPT__}
                    
                    **Task**: {task}
                    **Tools**: {self._get_tool_list(tool)}
                    **Configs**: {json.dumps(await ctx.export_configs(), ensure_ascii=False)}
                    **Additional Rules**: {self._rules}
                    **Response**:
                    """
                ),
            ),
        ]

        response = await self._openai.completion(messages=messages)

        await ctx.send_debug_message(
            f"[O1Planner@{tool.name}] Response: {response.choices[0].message.content}"
        )

        plan_response = self._parse_response(response.choices[0].message.content)

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
                sub_plan = await ExperimentalO1Planner(
                    openai_api_key=self._openai_api_key
                ).generate_plan(
                    ctx=ctx,
                    task=step.task,
                    tool=agent,
                )

            potential_tools = []

            for name in step.potential_tools:
                # in case the model returns `functions.[name]` instead of just `name`
                tool_name = name.split(".")[-1]
                if tool_name in self._fn_map:
                    potential_tools.append(self._fn_map[tool_name])

            steps.append(
                ExecutionStep(
                    task=step.task,
                    thought=step.thought,
                    potential_tools=potential_tools,
                    sub_plan=sub_plan,
                )
            )

        return Plan(goal=plan.goal, steps=steps, toolset=tool)
