import csv
import re
from typing import List, AsyncGenerator, Dict

from litellm.types.completion import (
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)

from npiai.llm import LLM
from npiai.context import Context


async def llm_summarize(
    ctx: Context,
    messages: List[ChatCompletionMessageParam],
) -> AsyncGenerator[Dict[str, str], None]:
    messages_copy = messages.copy()
    final_response_content = ""

    while True:
        response = await ctx.llm.acompletion(
            messages=messages_copy,
            max_tokens=4096,
            # use fixed temperature and seed to ensure deterministic results
            temperature=0.0,
            seed=42,
        )

        ctx.record(prompts=messages_copy, response=response)

        messages_copy.append(response.choices[0].message)

        content = response.choices[0].message.content
        match = re.match(r"```.*\n([\s\S]+?)(```|$)", content)

        if match:
            csv_table = match.group(1)
        else:
            csv_table = content

        final_response_content += csv_table

        if response.choices[0].finish_reason != "length":
            break

        messages_copy.append(
            ChatCompletionUserMessageParam(
                role="user",
                content="Continue generating the response.",
            ),
        )

    for row in csv.DictReader(final_response_content.splitlines(), delimiter=";"):
        yield row
