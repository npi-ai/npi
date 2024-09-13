import json
from typing import List

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel, Field

from npiai.context import Context
from npiai.utils import llm_tool_call
from npiai.core.tool import AgentTool
from npiai.core.base import BaseTool

from .base import BaseTaskTuner


__PROMPT__ = """
Your task is to elaborate on the provided brief by incorporating specific details and contextual information that will articulate the purpose and goals of the task. Draw parallels between this task and others that share common objectives, highlighting any shared principles or guidelines. Ensure that the task is articulated with precision, encompassing all critical details necessary for its successful execution.

Take into account the tools made available for this task and determine which are pertinent. Consider how these tools can be strategically utilized to optimize the task's execution. Where there are gaps in the provided information, prepare specific questions to ask the user to obtain the essential details. List these questions under the "Information Needed" section.

## Example

- Task: "Book a one-way flight from New York to London"
- Refined Task: \"""
As a travel agent, your role is to facilitate a customer in booking a one-way flight from New York to London. To proceed, engage with the customer to gather their preferred travel dates, desired departure times, and any airline preferences they may have. Utilize this information to identify and present the most suitable flight options, tailored to their specifications. Upon customer review, take the necessary steps to secure the booking according to the option they select.

Information Needed:
- Preferred travel dates
- Desired departure times
- Airline preferences
""\"

## Related Tasks
{related_tasks}

## Available Tools
{tools}
"""


class TaskResponse(BaseModel):
    refined_task: str = Field(
        description="Refined version of the task with additional details"
    )


class HistorianTuner(BaseTaskTuner):
    @staticmethod
    def _get_tool_list(tool: BaseTool) -> str:
        tools = tool.tool.tools if isinstance(tool, AgentTool) else tool.tools
        return json.dumps(tools)

    async def tune(
        self,
        ctx: Context,
        instruction: str,
        tool: BaseTool,
        related_tasks: List[str] | None = None,
    ) -> str:
        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=__PROMPT__.format(
                    tools=self._get_tool_list(tool),
                    related_tasks=json.dumps(related_tasks, ensure_ascii=False),
                ),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=instruction,
            ),
        ]

        response = await llm_tool_call(
            llm=ctx.llm,
            model=TaskResponse,
            tool=self.export,
            tool_description="Export the refined task",
            messages=messages,
        )

        return await self.export(response)

    async def export(self, response: TaskResponse) -> str:
        return response.refined_task
