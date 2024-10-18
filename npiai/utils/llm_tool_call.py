import json
from typing import List, Callable

from litellm.types.completion import ChatCompletionMessageParam
from pydantic import BaseModel

from npiai.llm import LLM
from .parse_npi_function import parse_npi_function


async def llm_tool_call(
    llm: LLM,
    tool: Callable,
    messages: List[ChatCompletionMessageParam],
) -> BaseModel:
    fn_reg = parse_npi_function(tool)

    if fn_reg.model is None:
        raise RuntimeError("Unable to modeling tool function")

    response = await llm.completion(
        messages=messages,
        tools=[fn_reg.get_tool_param()],
        max_tokens=4096,
        tool_choice={"type": "function", "function": {"name": fn_reg.name}},
    )

    response_message = response.choices[0].message
    tool_calls = response_message.get("tool_calls", None)

    if not tool_calls or tool_calls[0].function.name != fn_reg.name:
        raise RuntimeError("No tool call received")

    args = json.loads(tool_calls[0].function.arguments)

    # logger.debug(f"[{fn_reg.name}] Received: {args}")

    return fn_reg.model(**args)
