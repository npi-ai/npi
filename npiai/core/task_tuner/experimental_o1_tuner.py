import re
import json
from textwrap import dedent
from typing import List, Literal

from litellm.types.completion import ChatCompletionUserMessageParam


from npiai.context import Context
from npiai.core.tool import AgentTool
from npiai.core.base import BaseTool
from npiai.llm import OpenAI


from .base import BaseTaskTuner


__PROMPT__ = """
As a task tuner, your role is to refine the given task by incorporating relevant details and context that will clarify the purpose and objectives. Follow the guidelines below to enhance the task description:

1. **Review Related Tasks**: Compare this task to the related tasks, and identify any common themes or underlying rules that they share.
2. **Define the Agent's Role**: Clearly outline the role of the AI Agent in executing the task and how it can assist the user in achieving the desired outcome. Begin your response with "As a(n) [Agent's Role], your role is to...".
3. **Identify Critical Information**: Determine the essential information required to accomplish the task successfully. This may include specific details, preferences, or constraints that are crucial for the task's completion.
4. **Utilize Available Tools**: Take into account the tools made available for this task and determine which are pertinent. Consider how these tools can be strategically utilized to optimize the task's execution. 
5. **Ask Clarifying Questions**: Where there are gaps in the provided information, prepare specific questions to ask the user to obtain the essential details. List these questions under the "Information Needed" section.

## Example

**Original Task**: Book a one-way flight from New York to London
**Related Task**: ["Book a one-way flight from Los Angeles to New York", "Book a round-trip flight from London to Paris", ...]
**Tools**: [flight_search, payment_gateway, ticket_booking, ...]
**Refined Task**: As a travel agent, your role is to facilitate a customer in booking a one-way flight from New York to London. To proceed, engage with the customer to gather their preferred travel dates, desired departure times, and any airline preferences they may have. Utilize this information to identify and present the most suitable flight options, tailored to their specifications. Upon customer review, take the necessary steps to secure the booking according to the option they select.

Information Needed:
- Preferred travel dates
- Desired departure times
- Airline preferences
"""


class ExperimentalO1Tunner(BaseTaskTuner):
    def __init__(
        self,
        openai_api_key: str,
        o1_model: Literal["o1-preview", "o1-mini"] = "o1-preview",
    ):
        self.openai = OpenAI(model=o1_model, api_key=openai_api_key)

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
            ChatCompletionUserMessageParam(
                role="user",
                content=dedent(
                    f"""
                    {__PROMPT__}
                    
                    **Original Task**: {instruction}
                    **Related Task**: {json.dumps(related_tasks, ensure_ascii=False)}
                    **Tools**: {self._get_tool_list(tool)}
                    **Refined Task**:
                    """
                ),
            ),
        ]

        response = await self.openai.completion(messages=messages)

        content = response.choices[0].message.content

        if not content:
            return instruction

        # Remove the "Refined Task" header if present
        return re.sub(r"(\*\*)?Refined Task(\*\*)?:", "", content).strip()
