import asyncio
import csv
import json
import os
import sys
import traceback
from abc import ABC, abstractmethod
from typing import List, AsyncGenerator, Any

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from npiai import function, Context, FunctionTool
from npiai.utils import (
    llm_tool_call,
    llm_summarize,
    concurrent_task_runner,
)
from .prompts import (
    DEFAULT_COLUMN_INFERENCE_PROMPT,
    DEFAULT_COLUMN_SUMMARIZE_PROMPT,
)
from .types import (
    Column,
    SourceItem,
    SummaryItem,
    SummaryChunk,
)

__INDEX_COLUMN__ = Column(
    name="[[item_index]]",
    type="text",
    description="The index of the item in the list",
    prompt="Extract the index of the item in the list",
)


class BaseScraper(FunctionTool, ABC):
    name = "base_scraper"
    description = "Generic scraper tool"

    summarize_prompt: str = DEFAULT_COLUMN_SUMMARIZE_PROMPT
    infer_prompt: str = DEFAULT_COLUMN_INFERENCE_PROMPT

    @abstractmethod
    async def next_items(self, ctx: Context, count: int) -> List[SourceItem] | None: ...

    async def init_data(self, ctx: Context):
        pass

    async def summarize_stream(
        self,
        ctx: Context,
        output_columns: List[Column],
        batch_size: int = 1,
        limit: int = -1,
        concurrency: int = 1,
    ) -> AsyncGenerator[SummaryChunk, None]:
        """
        Summarize the content of a webpage into a csv table represented as a stream of item objects.

        Args:
            ctx: NPi context.
            output_columns: The columns of the output table. If not provided, use the `infer_columns` function to infer the columns.
            batch_size: The number of items to summarize in each batch. Default is 1.
            limit: The maximum number of items to summarize. If -1, all items are summarized.
            concurrency: The number of concurrent tasks to run. Default is 1.

        Returns:
            A stream of items. Each item is a dictionary with keys corresponding to the column names and values corresponding to the column values.
        """
        if limit == 0:
            return

        await self.init_data(ctx)

        # total items summarized
        count = 0
        # remaining items to summarize, excluding the items being summarized
        remaining = limit
        # batch index
        batch_index = 0

        lock = asyncio.Lock()

        async def run_batch(results_queue: asyncio.Queue[SummaryChunk]):
            nonlocal count, remaining, batch_index

            if limit != -1 and remaining <= 0:
                return

            async with lock:
                current_index = batch_index
                batch_index += 1

                # calculate the number of items to summarize in the current batch
                requested_count = (
                    min(batch_size, remaining) if limit != -1 else batch_size
                )
                # reduce the remaining count by the number of items in the current batch
                # so that the other tasks will not exceed the limit
                remaining -= requested_count

            data = await self.next_items(ctx=ctx, count=requested_count)

            if not data:
                await ctx.send_debug_message(f"[{self.name}] No more items found")
                return

            # await ctx.send_debug_message(
            #     f"[{self.name}] Parsed markdown: {parsed_result.markdown}"
            # )

            items = await self._summarize_llm_call(
                ctx=ctx,
                items=data,
                output_columns=output_columns,
            )

            await ctx.send_debug_message(f"[{self.name}] Summarized {len(items)} items")
            #
            # if not items:
            #     await ctx.send_debug_message(f"[{self.name}] No items summarized")
            #     return

            async with lock:
                items_slice = items[:requested_count] if limit != -1 else items
                summarized_count = len(items_slice)
                count += summarized_count
                # recalculate the remaining count in case summary returned fewer items than requested
                if summarized_count < requested_count:
                    remaining += requested_count - summarized_count

            await results_queue.put(
                SummaryChunk(
                    batch_id=current_index,
                    items=items_slice,
                )
            )

            await ctx.send_debug_message(
                f"[{self.name}] Summarized {count} items in total"
            )

            if limit == -1 or remaining > 0:
                await run_batch(results_queue)

        async for chunk in concurrent_task_runner(run_batch, concurrency):
            yield chunk

    @function
    async def summarize(
        self,
        ctx: Context,
        output_columns: List[Column],
        output_file: str,
        batch_size: int = 1,
        limit: int = -1,
        concurrency: int = 1,
    ) -> str:
        """
        Summarize the content of a webpage into a csv table.

        Args:
            ctx: NPi context.
            output_columns: The columns of the output table. If not provided, use the `infer_columns` function to infer the columns.
            output_file: The path to the output csv file.
            batch_size: The number of items to summarize in each batch. Default is 1.
            limit: The maximum number of items to summarize. If -1, all items are summarized.
            concurrency: The number of concurrent tasks to run. Default is 1.
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, "w", newline="") as f:  # type: Any
            column_names = [column["name"] for column in output_columns]
            writer = csv.DictWriter(f, fieldnames=column_names)
            writer.writeheader()
            f.flush()

            count = 0

            stream = self.summarize_stream(
                ctx=ctx,
                output_columns=output_columns,
                batch_size=batch_size,
                limit=limit,
                concurrency=concurrency,
            )

            async for chunk in stream:
                rows = [item["values"] for item in chunk["items"]]
                writer.writerows(rows)
                count += len(rows)
                f.flush()

        return f"Saved {count} items to {output_file}"

    @function
    async def infer_columns(
        self,
        ctx: Context,
        sample_size: int = 3,
        goal: str | None = None,
    ) -> List[Column] | None:
        """
        Infer the columns of the output table by finding the common nature of the items to summarize.

        Args:
            ctx: NPi context.
            sample_size: The number of items to use for inferring the columns.
            goal: The goal of the column inference.
        """
        await self.init_data(ctx)

        items = await self.next_items(ctx=ctx, count=sample_size)

        if not items:
            return None

        # await ctx.send_debug_message(
        #     f"[{self.name}] Parsed markdown: {parsed_result.markdown}"
        # )

        def callback(columns: List[Column]):
            """
            Callback with the inferred columns.

            Args:
                columns: The inferred columns.
            """
            return columns

        prompt = self.infer_prompt.format(
            goal=goal or "Extract essential details from the content"
        )

        items_data = [item["data"] for item in items]

        res = await llm_tool_call(
            llm=ctx.llm,
            tool=callback,
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=prompt,
                ),
                ChatCompletionUserMessageParam(
                    role="user",
                    content=json.dumps(items_data, ensure_ascii=False),
                ),
            ],
        )

        await ctx.send_debug_message(f"[{self.name}] Columns inference response: {res}")

        return callback(**res.model_dump())

    async def _summarize_llm_call(
        self,
        ctx: Context,
        items: List[SourceItem],
        output_columns: List[Column],
    ) -> List[SummaryItem]:
        """
        Summarize the content of a webpage into a table using LLM.

        Args:
            ctx: NPi context.
            items: The items to summarize.
            output_columns: The columns of the output table.

        Returns:
            The summarized items as a list of dictionaries.
        """

        # add id column to the output columns
        output_columns_with_index = [__INDEX_COLUMN__, *output_columns]

        items_with_index = [
            {"index": i, "data": item["data"]} for i, item in enumerate(items)
        ]

        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=self.summarize_prompt.format(
                    column_defs=json.dumps(
                        output_columns_with_index, ensure_ascii=False
                    )
                ),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=json.dumps(items_with_index, ensure_ascii=False),
            ),
        ]

        results = []

        try:
            async for row in llm_summarize(ctx.llm, messages):
                index = int(row.pop(__INDEX_COLUMN__["name"]))
                results.append(
                    SummaryItem(
                        hash=items[index]["hash"],
                        values=row,
                    )
                )
        except Exception as e:
            print(
                f"Error parsing the response: {traceback.format_exc()}",
                file=sys.stderr,
            )
            await ctx.send_error_message(f"Error parsing the response: {str(e)}")

        return results
