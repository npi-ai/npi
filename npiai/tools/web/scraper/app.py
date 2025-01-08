import asyncio
import csv
import hashlib
import json
import os
import re
import sys
import traceback
from pathlib import Path
from textwrap import dedent
from typing import List, AsyncGenerator, Any, Iterable, Set
from markdownify import MarkdownConverter

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from playwright.async_api import TimeoutError

from npiai import function, BrowserTool, Context
from npiai.core import NavigatorAgent
from npiai.utils import (
    is_cloud_env,
    llm_tool_call,
    llm_summarize,
    CompactMarkdownConverter,
    concurrent_task_runner,
)
from .prompts import (
    MULTI_COLUMN_INFERENCE_PROMPT,
    MULTI_COLUMN_SCRAPING_PROMPT,
    SINGLE_COLUMN_INFERENCE_PROMPT,
    SINGLE_COLUMN_SCRAPING_PROMPT,
)
from .types import (
    Column,
    ScrapingType,
    SummaryItem,
    SummaryChunk,
    ConversionResult,
)

__ID_COLUMN__ = Column(
    name="[[item_id]]",
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

    markdown_converter: MarkdownConverter = CompactMarkdownConverter()

    # The maximum number of items to summarize in a single batch
    _batch_size: int

    # all items loaded flag
    _all_items_loaded: bool = False

    _navigator: NavigatorAgent

    # asyncio lock to prevent concurrent access to the webpage
    # to avoid retrieving the same items multiple times
    _webpage_access_lock: asyncio.Lock

    def __init__(self, batch_size: int = 10, **kwargs):
        super().__init__(**kwargs)
        self._navigator = NavigatorAgent(
            playwright=self.playwright,
        )
        self._batch_size = batch_size
        self._webpage_access_lock = asyncio.Lock()
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
        # reset the flag when starting a new scraping task
        self._all_items_loaded = False

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

        lock = asyncio.Lock()

        skip_item_hashes_set = set(skip_item_hashes) if skip_item_hashes else None

        async def run_batch(results_queue: asyncio.Queue[SummaryChunk]):
            nonlocal count, remaining, batch_index

            if (limit != -1 and remaining <= 0) or self._all_items_loaded:
                return

            async with lock:
                current_index = batch_index
                batch_index += 1

                # calculate the number of items to summarize in the current batch
                requested_count = (
                    min(self._batch_size, remaining) if limit != -1 else -1
                )
                # reduce the remaining count by the number of items in the current batch
                # so that the other tasks will not exceed the limit
                remaining -= requested_count

            parsed_result = await self._convert(
                ancestor_selector=ancestor_selector,
                items_selector=items_selector,
                limit=requested_count,
                skip_item_hashes=skip_item_hashes_set,
            )

            if not parsed_result:
                await ctx.send_debug_message(f"[{self.name}] No more items found")
                return

            # await ctx.send_debug_message(
            #     f"[{self.name}] Parsed markdown: {parsed_result.markdown}"
            # )

            items = await self._summarize_llm_call(
                ctx=ctx,
                parsed_result=parsed_result,
                output_columns=output_columns,
                scraping_type=scraping_type,
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
                {
                    "batch_id": current_index,
                    "matched_hashes": parsed_result.matched_hashes,
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

                await run_batch(results_queue)

        async for chunk in concurrent_task_runner(run_batch, concurrency):
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
        goal: str | None = None,
    ) -> List[Column] | None:
        """
        Infer the columns of the output table by finding the common nature of the items to summarize.

        Args:
            ctx: NPi context.
            url: The URL to open.
            scraping_type: The type of scraping to perform. If 'single', infer the columns based on a single item. If 'list-like', infer the columns based on a list of items.
            ancestor_selector: The selector of the ancestor element containing the items to summarize. If None, the 'body' element is used.
            items_selector: The selector of the items to summarize. If None, all the children of the ancestor element are used.
            goal: The goal of the column inference.
        """

        await self.load_page(
            url,
            timeout=3000,
            wait_for_selector=items_selector,
        )

        if not ancestor_selector:
            ancestor_selector = "body"

        parsed_result = await self._convert(
            ancestor_selector=ancestor_selector,
            items_selector=items_selector,
            limit=3,
        )

        if not parsed_result:
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

        prompt = (
            MULTI_COLUMN_INFERENCE_PROMPT
            if scraping_type == "list-like"
            else SINGLE_COLUMN_INFERENCE_PROMPT
        ).format(goal=goal or "Extract essential details from the content")

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

    async def _convert(
        self,
        ancestor_selector: str,
        items_selector: str | None,
        limit: int = -1,
        skip_item_hashes: Set[str] | None = None,
    ) -> ConversionResult | None | None:
        async with self._webpage_access_lock:
            if self._all_items_loaded:
                return None

            # convert relative links to absolute links
            await self._process_relative_links()

            if items_selector is None:
                res = await self._convert_ancestor(ancestor_selector, skip_item_hashes)
            else:
                res = await self._convert_items(items_selector, limit, skip_item_hashes)

            if not res:
                self._all_items_loaded = True

            return res

    async def _convert_items(
        self,
        items_selector: str,
        limit: int = -1,
        skip_item_hashes: List[str] | None = None,
    ) -> ConversionResult | None | None:
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
                timeout=3_000,
            )
        except TimeoutError:
            return None

        sections = []
        hashes = []
        matched_hashes = []
        count = 0

        # use element handles here to snapshot the items
        for elem in await locator.element_handles():
            html = await elem.evaluate(
                """
                async (elem) => {
                    elem.scrollIntoView();
                    elem.setAttribute('data-npi-visited', 'true');
                    
                    const contentLength = elem.textContent?.replace(/\\s/g, '').length || 0;
                    
                    if (contentLength > 10) {
                        return elem.outerHTML;
                    }
                    
                    // in case the page uses lazy loading,
                    // wait for the content to be loaded
                    
                    return new Promise((resolve) => {
                        setTimeout(() => {
                            resolve(elem.outerHTML);
                        }, 300);
                    });
                }
                """
            )

            if not html:
                continue

            markdown, md5 = self._html_to_md_and_hash(html)

            if skip_item_hashes and md5 in skip_item_hashes:
                matched_hashes.append(md5)
                continue

            sections.append(f'<section id="{count}">\n{markdown}\n</section>')
            hashes.append(md5)
            count += 1

            if count == limit:
                break

        if not count:
            return None

        return ConversionResult(
            markdown="\n".join(sections),
            hashes=hashes,
            matched_hashes=matched_hashes,
        )

    async def _convert_ancestor(
        self,
        ancestor_selector: str,
        skip_item_hashes: Set[str] | None = None,
    ) -> ConversionResult | None | None:
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
        matched_hashes = []
        count = 0

        for html in htmls:
            markdown, md5 = self._html_to_md_and_hash(html)

            if skip_item_hashes and md5 in skip_item_hashes:
                matched_hashes.append(md5)
                continue

            sections.append(f'<section id="{count}">\n{markdown}\n</section>')
            hashes.append(md5)
            count += 1

        if not count:
            return None

        return ConversionResult(
            markdown="\n".join(sections),
            hashes=hashes,
            matched_hashes=matched_hashes,
        )

    def _html_to_md_and_hash(self, html: str):
        markdown = re.sub(r"\n+", "\n", self.markdown_converter.convert(html)).strip()
        md5 = hashlib.md5(markdown.encode()).hexdigest()
        return markdown, md5

    async def _summarize_llm_call(
        self,
        ctx: Context,
        parsed_result: ConversionResult,
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

        prompt = (
            MULTI_COLUMN_SCRAPING_PROMPT
            if scraping_type == "list-like"
            else SINGLE_COLUMN_SCRAPING_PROMPT
        )

        # add id column to the output columns
        output_columns_with_id = [__ID_COLUMN__, *output_columns]

        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=prompt.format(
                    column_defs=json.dumps(output_columns_with_id, ensure_ascii=False)
                ),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=parsed_result.markdown,
            ),
        ]

        results = []

        try:
            async for row in llm_summarize(ctx.llm, messages):
                index = int(row.pop(__ID_COLUMN__["name"]))
                results.append(
                    SummaryItem(
                        hash=parsed_result.hashes[index],
                        values=row,
                    )
                )
        except Exception as e:
            print(
                f"Error parsing the response: {traceback.format_exc()}",
                file=sys.stderr,
            )
            await ctx.send_error_message(
                f"[{self.name}] Error parsing the response: {str(e)}"
            )

        return results

    async def _load_more(
        self,
        ctx: Context,
        ancestor_selector: str,
        items_selector: str | None,
        pagination_button_selector: str | None = None,
    ):
        async with self._webpage_access_lock:
            unvisited_items_selector = (
                items_selector or "*"
            ) + ":not([data-npi-visited])"

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
                await ctx.send_debug_message(
                    f"[{self.name}] Scrolled to load more items"
                )
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
