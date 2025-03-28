import json
from typing import List, Callable, Awaitable, TYPE_CHECKING

from litellm.types.completion import ChatCompletionMessageParam

from .parse_npi_function import parse_npi_function

if TYPE_CHECKING:
    from npiai.context import Context


async def llm_tool_call[
    T
](
    ctx: "Context",
    tool: Callable[..., Awaitable[T]],
    messages: List[ChatCompletionMessageParam],
) -> T:
    fn_reg = parse_npi_function(tool)

    if fn_reg.model is None:
        raise RuntimeError("Unable to modeling tool function")

    response = await ctx.llm.acompletion(
        messages=messages,
        tools=[fn_reg.get_tool_param()],
        max_tokens=4096,
        tool_choice={"type": "function", "function": {"name": fn_reg.name}},
    )

    response_message = response.choices[0].message
    tool_calls = response_message.get("tool_calls", None)

    if not tool_calls or tool_calls[0].function.name != fn_reg.name:
        raise RuntimeError("No tool call received")

    ctx.record(prompts=messages, response=response)

    args = json.loads(tool_calls[0].function.arguments)

    # logger.debug(f"[{fn_reg.name}] Received: {args}")

    model = fn_reg.model(**args)

    return await tool(**model.model_dump())
