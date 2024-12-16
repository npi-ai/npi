import csv
import json
import re
import os
import asyncio
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, AsyncGenerator, Literal, Any, Iterable, Set
from typing_extensions import TypedDict, Annotated
from textwrap import dedent
from playwright.async_api import TimeoutError

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from npiai import function, BrowserTool, Context
from npiai.core import NavigatorAgent
from npiai.utils import is_cloud_env, llm_tool_call, html_to_markdown

from .prompts import (
    MULTI_COLUMN_INFERENCE_PROMPT,
    MULTI_COLUMN_SCRAPING_PROMPT,
    SINGLE_COLUMN_INFERENCE_PROMPT,
    SINGLE_COLUMN_SCRAPING_PROMPT,
)

ScrapingType = Literal["single", "list-like"]


class Column(TypedDict):
    name: Annotated[str, "Name of the column"]
    type: Annotated[Literal["text", "link", "image"], "Type of the column"]
    description: Annotated[str, "A brief description of the column"]
    prompt: Annotated[
        str | None, "A step-by-step prompt on how to extract the column data"
    ]


class SummaryItem(TypedDict):
    hash: str
    values: Dict[str, str]


class SummaryChunk(TypedDict):
    batch_id: int
    items: List[SummaryItem]


@dataclass
class ParsedResult:
    markdown: str
    hashes: List[str]


__ID_COLUMN__ = Column(
    name="id",
    type="text",
    description="Unique identifier for each item",
    prompt="Fill in the unique identifier for the corresponding <section> that represents the item",
)


class Scraper(BrowserTool):
    name = "scraper"
    description = (
        "A web scraper agent that can summarize the content of a webpage into a table"
    )
    system_prompt = dedent(
        """
        You are a general web scraper agent helping user summarize the content of a webpage into a table.
        """
    )

    # The maximum number of items to summarize in a single batch
    _batch_size: int

    _navigator: NavigatorAgent

    def __init__(self, batch_size: int = 10, **kwargs):
        super().__init__(**kwargs)
        self._navigator = NavigatorAgent(
            playwright=self.playwright,
        )
        self._batch_size = batch_size
        self.add_tool(self._navigator)

    @classmethod
    def from_context(cls, ctx: Context) -> "Scraper":
        if not is_cloud_env():
            raise RuntimeError(
                "Scraper tool can only be initialized from context in the NPi cloud environment"
            )
        return cls()

    async def summarize_stream(
        self,
        ctx: Context,
        url: str,
        output_columns: List[Column],
        scraping_type: ScrapingType,
        ancestor_selector: str | None = None,
        items_selector: str | None = None,
        pagination_button_selector: str | None = None,
        limit: int = -1,
        concurrency: int = 1,
        skip_item_hashes: Iterable[str] | None = None,
    ) -> AsyncGenerator[SummaryChunk, None]:
        """
        Summarize the content of a webpage into a csv table represented as a stream of item objects.

        Args:
            ctx: NPi context.
            url: The URL to open.
            output_columns: The columns of the output table. If not provided, use the `infer_columns` function to infer the columns.
            scraping_type: The type of scraping to perform. If 'single', summarize the content into a single row. If 'list-like', summarize the content into multiple rows.
            ancestor_selector: The selector of the ancestor element containing the items to summarize. If None, the 'body' element is used.
            items_selector: The selector of the items to summarize. If None, all the children of the ancestor element are used.
            pagination_button_selector: The selector of the pagination button (e.g., the "Next Page" button) to load more items. Used when the items are paginated. By default, the tool will scroll to load more items.
            limit: The maximum number of items to summarize. If -1, all items are summarized.
            concurrency: The number of concurrent tasks to run. Default is 1.
            skip_item_hashes: A list of hashes of items to skip. If provided, the items with these hashes will be skipped.

        Returns:
            A stream of items. Each item is a dictionary with keys corresponding to the column names and values corresponding to the column values.
        """
        if limit == 0:
            return

        if scraping_type == "single":
            limit = 1

        await self.load_page(url)

        if not ancestor_selector:
            ancestor_selector = "body"

        # total items summarized
        count = 0
        # remaining items to summarize, excluding the items being summarized
        remaining = limit
        # batch index
        batch_index = 0

        results_queue: asyncio.Queue[SummaryChunk] = asyncio.Queue()

        skip_item_hashes_set = set(skip_item_hashes) if skip_item_hashes else None

        async def run_batch():
            nonlocal count, remaining, batch_index

            if limit != -1 and remaining <= 0:
                return

            current_index = batch_index
            batch_index += 1

            # calculate the number of items to summarize in the current batch
            requested_count = min(self._batch_size, remaining) if limit != -1 else -1
            # reduce the remaining count by the number of items in the current batch
            # so that the other tasks will not exceed the limit
            remaining -= requested_count

            parsed_result = await self._parse(
                ancestor_selector=ancestor_selector,
                items_selector=items_selector,
                limit=requested_count,
                skip_item_hashes=skip_item_hashes_set,
            )

            if not parsed_result:
                await ctx.send_debug_message(f"[{self.name}] No more items found")
                return

            await ctx.send_debug_message(
                f"[{self.name}] Parsed markdown: {parsed_result.markdown}"
            )

            items = await self._llm_summarize(
                ctx=ctx,
                parsed_result=parsed_result,
                output_columns=output_columns,
                scraping_type=scraping_type,
            )

            await ctx.send_debug_message(f"[{self.name}] Summarized {len(items)} items")

            if not items:
                await ctx.send_debug_message(f"[{self.name}] No items summarized")
                return

            items_slice = items[:requested_count] if limit != -1 else items
            summarized_count = len(items_slice)
            count += summarized_count
            # correct the remaining count in case summary returned fewer items than requested
            if summarized_count < requested_count:
                remaining += requested_count - summarized_count

            await results_queue.put(
                {
                    "batch_id": current_index,
                    "items": items_slice,
                }
            )

            await ctx.send_debug_message(
                f"[{self.name}] Summarized {count} items in total"
            )

            if limit == -1 or remaining > 0:
                await self._load_more(
                    ctx,
                    ancestor_selector,
                    items_selector,
                    pagination_button_selector,
                )

                await run_batch()

        # number of running tasks
        running_task_count = 0

        async def task_runner():
            nonlocal running_task_count
            running_task_count += 1
            await run_batch()
            running_task_count -= 1

        # schedule tasks
        tasks = [asyncio.create_task(task_runner()) for _ in range(concurrency)]

        # wait for the first task to start
        while running_task_count == 0:
            await asyncio.sleep(0.1)

        # collect results
        while running_task_count > 0 or not results_queue.empty():
            chunk = await results_queue.get()
            yield chunk

        # wait for all tasks to finish
        await asyncio.gather(*tasks)

        # consume the remaining items if any
        while not results_queue.empty():
            chunk = await results_queue.get()
            yield chunk

    @function
    async def summarize(
        self,
        ctx: Context,
        url: str,
        output_columns: List[Column],
        scraping_type: ScrapingType,
        ancestor_selector: str | None = None,
        items_selector: str | None = None,
        pagination_button_selector: str | None = None,
        output_file: Path | str | None = None,
        limit: int = -1,
        concurrency: int = 1,
        skip_item_hashes: List[str] | None = None,
    ) -> str:
        """
        Summarize the content of a webpage into a csv table.

        Args:
            ctx: NPi context.
            url: The URL to open.
            output_columns: The columns of the output table. If not provided, use the `infer_columns` function to infer the columns.
            scraping_type: The type of scraping to perform. If 'single', summarize the content into a single row. If 'list-like', summarize the content into multiple rows.
            ancestor_selector: The selector of the ancestor element containing the items to summarize. If None, the 'body' element is used.
            items_selector: The selector of the items to summarize. If None, all the children of the ancestor element are used.
            pagination_button_selector: The selector of the pagination button (e.g., the "Next Page" button) to load more items. Used when the items are paginated. By default, the tool will scroll to load more items.
            output_file: The file path to save the output. If None, the output is saved to 'scraper_output.json'.
            limit: The maximum number of items to summarize. If -1, all items are summarized.
            concurrency: The number of concurrent tasks to run. Default is 1.
            skip_item_hashes: A list of hashes of items to skip. If provided, the items with these hashes will be skipped.
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
                url=url,
                output_columns=output_columns,
                scraping_type=scraping_type,
                ancestor_selector=ancestor_selector,
                items_selector=items_selector,
                pagination_button_selector=pagination_button_selector,
                limit=limit,
                concurrency=concurrency,
                skip_item_hashes=skip_item_hashes,
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
        url: str,
        scraping_type: ScrapingType,
        ancestor_selector: str | None = None,
        items_selector: str | None = None,
    ) -> List[Column] | None:
        """
        Infer the columns of the output table by finding the common nature of the items to summarize.

        Args:
            ctx: NPi context.
            url: The URL to open.
            scraping_type: The type of scraping to perform. If 'single', infer the columns based on a single item. If 'list-like', infer the columns based on a list of items.
            ancestor_selector: The selector of the ancestor element containing the items to summarize. If None, the 'body' element is used.
            items_selector: The selector of the items to summarize. If None, all the children of the ancestor element are used.
        """

        await self.load_page(url)

        if not ancestor_selector:
            ancestor_selector = "body"

        parsed_result = await self._parse(
            ancestor_selector=ancestor_selector,
            items_selector=items_selector,
            limit=10,
        )

        if not parsed_result:
            return None

        await ctx.send_debug_message(
            f"[{self.name}] Parsed markdown: {parsed_result.markdown}"
        )

        def callback(columns: List[Column]):
            """
            Callback with the inferred columns.

            Args:
                columns: The inferred columns.
            """
            return columns

        prompt = (
            MULTI_COLUMN_INFERENCE_PROMPT
            if scraping_type == "list-like"
            else SINGLE_COLUMN_INFERENCE_PROMPT
        )

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
                    content=parsed_result.markdown,
                ),
            ],
        )

        await ctx.send_debug_message(f"[{self.name}] Columns inference response: {res}")

        return callback(**res.model_dump())

    async def _parse(
        self,
        ancestor_selector: str,
        items_selector: str | None,
        limit: int = -1,
        skip_item_hashes: Set[str] | None = None,
    ) -> ParsedResult | None | None:
        # convert relative links to absolute links
        await self._process_relative_links()

        if items_selector is None:
            return await self._parse_ancestor(ancestor_selector, skip_item_hashes)
        else:
            return await self._parse_items(items_selector, limit, skip_item_hashes)

    async def _parse_items(
        self,
        items_selector: str,
        limit: int = -1,
        skip_item_hashes: List[str] | None = None,
    ) -> ParsedResult | None | None:
        """
        Get the markdown content of the items to summarize

        Args:
            items_selector: The selector of the items to summarize.
            limit: The maximum number of items to summarize.
            skip_item_hashes: A set of hashes of items to skip.

        Returns:
            The markdown content of the items to summarize.
        """
        if limit == 0:
            return None

        locator = self.playwright.page.locator(
            items_selector + ":not([data-npi-visited])"
        )

        # wait for the first unvisited item to be attached to the DOM
        try:
            await locator.first.wait_for(
                state="attached",
                timeout=30_000,
            )
        except TimeoutError:
            return None

        sections = []
        hashes = []
        count = 0
        marking_tasks = []

        # use element handles here to snapshot the items
        for elem in await locator.element_handles():
            html = await elem.evaluate("elem => elem.outerHTML")
            markdown, md5 = self._html_to_md_and_hash(html)

            if skip_item_hashes and md5 in skip_item_hashes:
                continue

            # mark the item as visited
            marking_tasks.append(
                asyncio.create_task(
                    elem.evaluate(
                        "elem => elem.setAttribute('data-npi-visited', 'true')"
                    )
                )
            )

            sections.append(f'<section id="{count}">\n{markdown}\n</section>')
            hashes.append(md5)
            count += 1

            if count == limit:
                break

        if not count:
            return None

        await asyncio.gather(*marking_tasks)

        return ParsedResult(markdown="\n".join(sections), hashes=hashes)

    async def _parse_ancestor(
        self,
        ancestor_selector: str,
        skip_item_hashes: Set[str] | None = None,
    ) -> ParsedResult | None | None:
        """
        Get the markdown content of the ancestor element

        Args:
            ancestor_selector: The selector of the ancestor element.
            skip_item_hashes: A set of hashes of items to skip.

        Returns:
            The markdown content of the ancestor element.
        """

        # check if there are mutation records
        htmls = await self.playwright.page.evaluate(
            """
            () => {
                const { addedNodes } = window;
                
                if (addedNodes?.length) {
                    window.addedNodes = [];
                    return addedNodes.map(node => node.outerHTML);
                }
                
                return null;
            }
            """,
        )

        if htmls is None:
            locator = self.playwright.page.locator(ancestor_selector)

            # wait for the ancestor element to be attached to the DOM
            try:
                await locator.first.wait_for(state="attached", timeout=30_000)
            except TimeoutError:
                return None

            if not await locator.count():
                return None

            htmls = []

            # use all ancestors here to avoid missing any items
            for elem in await locator.all():
                htmls.append(await elem.evaluate("elem => elem.outerHTML"))

        sections = []
        hashes = []
        count = 0

        for html in htmls:
            markdown, md5 = self._html_to_md_and_hash(html)

            if skip_item_hashes and md5 in skip_item_hashes:
                continue

            sections.append(f'<section id="{count}">\n{markdown}\n</section>')
            hashes.append(md5)
            count += 1

        if not count:
            return None

        return ParsedResult(markdown="\n".join(sections), hashes=hashes)

    @staticmethod
    def _html_to_md_and_hash(html):
        markdown = html_to_markdown(html)
        md5 = hashlib.md5(markdown.encode()).hexdigest()
        return markdown, md5

    async def _llm_summarize(
        self,
        ctx: Context,
        parsed_result: ParsedResult,
        output_columns: List[Column],
        scraping_type: ScrapingType,
    ) -> List[SummaryItem]:
        """
        Summarize the content of a webpage into a table using LLM.

        Args:
            ctx: NPi context.
            parsed_result: The parsed result containing the markdown content of the items to summarize.
            output_columns: The columns of the output table.
            scraping_type: The type of scraping to perform. If 'single', summarize the content into a single row. If 'list-like', summarize the content into multiple rows.

        Returns:
            The summarized items as a list of dictionaries.
        """

        if scraping_type == "list-like":
            prompt = MULTI_COLUMN_SCRAPING_PROMPT
            output_columns = [__ID_COLUMN__, *output_columns]
        else:
            prompt = SINGLE_COLUMN_SCRAPING_PROMPT

        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=prompt.format(
                    column_defs=json.dumps(output_columns, ensure_ascii=False)
                ),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=parsed_result.markdown,
            ),
        ]

        final_response_content = ""

        while True:
            response = await ctx.llm.completion(
                messages=messages,
                max_tokens=4096,
                # use fixed temperature and seed to ensure deterministic results
                temperature=0.0,
                seed=42,
            )

            messages.append(response.choices[0].message)

            content = response.choices[0].message.content
            match = re.match(r"```.*\n([\s\S]+?)(```|$)", content)

            if match:
                csv_table = match.group(1)
            else:
                csv_table = content

            final_response_content += csv_table

            await ctx.send_debug_message(
                f"[{self.name}] Received summarization response: {content}"
            )

            if response.choices[0].finish_reason != "length":
                break

            messages.append(
                ChatCompletionUserMessageParam(
                    role="user",
                    content="Continue generating the response.",
                ),
            )

        results = []

        for row in csv.DictReader(final_response_content.splitlines()):
            index = int(row.pop("id"))
            results.append(SummaryItem(hash=parsed_result.hashes[index], values=row))

        return results

    async def _load_more(
        self,
        ctx: Context,
        ancestor_selector: str,
        items_selector: str | None,
        pagination_button_selector: str | None = None,
    ):
        unvisited_items_selector = (items_selector or "*") + ":not([data-npi-visited])"

        # check if there are unvisited items
        has_unvisited_items = await self.playwright.page.evaluate(
            f"selector => !!document.querySelector(selector)",
            unvisited_items_selector,
        )

        if has_unvisited_items:
            await ctx.send_debug_message(
                f"[{self.name}] Found unvisited items, skipping loading more items"
            )
            return

        # attach mutation observer to the ancestor element
        await self.playwright.page.evaluate(
            """
            ([ancestor_selector, items_selector]) => {
                window.addedNodes = [];
                
                window.npiObserver = new MutationObserver((records) => {
                    for (const record of records) {
                        for (const addedNode of record.addedNodes) {
                            if (addedNode.nodeType === Node.ELEMENT_NODE &&
                                (addedNode.matches(items_selector) || addedNode.querySelector(items_selector))
                            ) {
                                window.addedNodes.push(addedNode);
                            }
                        }
                    }
                });
                
                window.npiObserver.observe(
                    document.querySelector(ancestor_selector), 
                    { childList: true, subtree: true }
                );
            }
            """,
            [ancestor_selector, items_selector or "*"],
        )

        more_content_loaded = False

        # check if the page is scrollable
        # if so, scroll to load more items
        if await self.is_scrollable():
            await self.playwright.page.evaluate(
                """
                (ancestor_selector) => {
                    let elem;
                    const items = document.querySelectorAll('[data-npi-visited]');
                    
                    if (items.length) {
                        const elem = items[items.length - 1];
                        elem?.scrollIntoView();
                    } else {
                        const elem = document.querySelector(ancestor_selector);
                        elem?.scrollIntoView({ block: 'end' });
                    }
                }
                """,
                ancestor_selector,
            )
            await ctx.send_debug_message(f"[{self.name}] Scrolled to load more items")
            await self.playwright.page.wait_for_timeout(3000)
            more_content_loaded = await self.playwright.page.evaluate(
                "() => !!window.addedNodes?.length",
            )

        if not more_content_loaded and pagination_button_selector:
            handle = await self.playwright.page.evaluate_handle(
                "selector => document.querySelector(selector)",
                pagination_button_selector,
            )

            elem = handle.as_element()

            if not elem:
                await ctx.send_debug_message(
                    f"[{self.name}] Pagination button not found"
                )
                return

            await self.click(elem)
            await ctx.send_debug_message(f"[{self.name}] Clicked pagination button")
            await self.playwright.page.wait_for_timeout(3000)

        # clear the mutation observer
        await self.playwright.page.evaluate(
            "() => { window.npiObserver?.disconnect(); }"
        )

    async def _process_relative_links(self):
        await self.playwright.page.evaluate(
            """
            [...document.querySelectorAll('a[href]')].forEach(a => {
                const href = a.getAttribute('href');
                
                if (!href) {
                    return;
                }
                
                const url = new URL(href, window.location.href);
                a.setAttribute('href', url.href);
            });
            """
        )
