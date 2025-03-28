import json
from textwrap import dedent

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from npiai.utils import llm_tool_call
from npiai.context import Context


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


async def llm_assert(
    ctx: Context,
    output: str,
    expectations: str,
    constraints: str = None,
):
    async def report(passed: bool, reason: str | None = None):
        """
        Report the result of the assertion.

        Args:
            passed: Whether the assertion passed.
            reason: The reason for the assertion failure.
        """
        if not passed:
            reason = dedent(
                f"""
                {reason}
                
                Agent Output: {output}
                Expectations: {expectations}
                """.strip()
            )
        assert passed, reason

    return await llm_tool_call(
        ctx=ctx,
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
