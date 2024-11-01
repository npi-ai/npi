import json
import os
from textwrap import dedent

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from npiai.utils import llm_tool_call
from npiai.llm import OpenAI


__PROMPT__ = """
Your task is to check the agent's output to see if it satisfies the expectations following the constraints (if provided).

If the output is correct, call the `report` function with the argument `{"passed": True}`.
Otherwise, call the `report` function with the argument `{"passed": False, "reason": "Your reason here."}`.

## Provided Information

You are given the agent's output and the expectations in a JSON format:
```json
{
    "agent_output": "The agent's output.",
    "expectations": "The expectations."
    "constraints": "The constraints for the comparison."
}
```
"""


def report(passed: bool, reason: str | None = None):
    """
    Report the result of the assertion.

    Args:
        passed: Whether the assertion passed.
        reason: The reason for the assertion failure.
    """
    assert passed, reason


async def llm_assert(output: str, expectations: str, constraints: str = None):
    res = await llm_tool_call(
        llm=OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", None),
            model="gpt-4o",
        ),
        tool=report,
        messages=[
            ChatCompletionSystemMessageParam(
                role="system",
                content=__PROMPT__,
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=json.dumps(
                    {
                        "agent_output": output,
                        "expectations": expectations,
                        "constraints": constraints,
                    }
                ),
            ),
        ],
    )

    passed = res.passed
    reason = res.reason

    if not passed:
        reason = dedent(
            f"""
            {res.reason}
            
            Agent Output: {output}
            Expectations: {expectations}
            """.strip()
        )

    return report(passed, reason)
