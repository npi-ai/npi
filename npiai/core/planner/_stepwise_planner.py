import json
from typing import List

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import create_model, Field

from npiai.context import Context
from npiai.types import FunctionRegistration
from npiai.utils import sanitize_schema

from ._base import BasePlanner

__PROMPT__ = """
Create a step-by-step plan to complete the given task using a designated set of tools. Identify the most appropriate tools from below, and articulate the plan clearly, concisely, and in logical order. Upon completion of the plan, call the `execute` function with the arranged steps as its argument.

## Available Tools
{tools}
"""


class StepwisePlanner(BasePlanner):
    async def generate_plan(
        self,
        ctx: Context,
        instruction: str,
        functions: List[FunctionRegistration],
    ) -> List[str]:
        tools = "\n".join(f"- {fn.name}: {fn.description}" for fn in functions)
        model = create_model(
            "StepwisePlanner",
            plan=(
                List[str],
                Field(description="A step-by-step execution plan"),
            ),
        )
        fn_reg = FunctionRegistration(
            fn=self.execute,
            name="execute",
            description="make up user configuration criteria",
            ctx_variables=[],
            model=model,
            schema=sanitize_schema(model),
        )
        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=__PROMPT__.format(tools=tools),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=instruction,
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

        if not tool_calls:
            raise RuntimeError("No tool call received to devise an execution plan")

        args = json.loads(tool_calls[0].function.arguments)

        await ctx.send_debug_message(f"[StepwisePlanner] Received {args}]")

        return await self.execute(**args)

    async def execute(self, plan: List[str]):
        return plan
