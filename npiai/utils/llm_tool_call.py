import json
from typing import List, TypeVar
from litellm.types.completion import ChatCompletionMessageParam
from pydantic import BaseModel

from npiai.llm import LLM
from npiai.types.function_registration import ToolFunction, FunctionRegistration
from npiai.utils import sanitize_schema, logger


_T = TypeVar("_T", bound=BaseModel)


async def llm_tool_call(
    llm: LLM,
    model: type[_T],
    tool: ToolFunction,
    tool_description: str,
    messages: List[ChatCompletionMessageParam],
) -> _T:
    tool_name = tool.__name__
    fn_reg = FunctionRegistration(
        fn=tool,
        name=tool_name,
        description=tool_description,
        model=model,
        schema=sanitize_schema(model),
    )

    response = await llm.completion(
        messages=messages,
        tools=[fn_reg.get_tool_param()],
        max_tokens=4096,
        tool_choice={"type": "function", "function": {"name": tool_name}},
    )

    response_message = response.choices[0].message
    tool_calls = response_message.get("tool_calls", None)

    if not tool_calls or tool_calls[0].function.name != tool_name:
        raise RuntimeError("No tool call received")

    args = json.loads(tool_calls[0].function.arguments)

    logger.debug(f"[{tool_name}] Received: {args}")

    return model(**args)
