import csv
import json
import re
import os
from typing import List, Dict, AsyncGenerator, Literal
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
    prompt: Annotated[
        str | None, "A step-by-step prompt on how to extract the column data"
    ]


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
    ) -> AsyncGenerator[List[Dict[str, str]], None]:
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

        count = 0

        while True:
            remaining = min(self._batch_size, limit - count) if limit != -1 else -1

            md = await self._get_md(
                ctx=ctx,
                ancestor_selector=ancestor_selector,
                items_selector=items_selector,
                limit=remaining,
            )

            if not md:
                break

            items = await self._llm_summarize(
                ctx=ctx,
                md=md,
                output_columns=output_columns,
                scraping_type=scraping_type,
            )

            await ctx.send_debug_message(f"[{self.name}] Summarized {len(items)} items")

            if not items:
                break

            items_slice = items[:remaining] if limit != -1 else items
            count += len(items_slice)

            yield items_slice

            await ctx.send_debug_message(
                f"[{self.name}] Summarized {count} items in total"
            )

            if limit != -1 and count >= limit:
                break

            await self._load_more(
                ctx,
                ancestor_selector,
                items_selector,
                pagination_button_selector,
            )

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
        output_file: str | None = None,
        limit: int = -1,
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
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, "w", newline="") as f:
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
            )

            async for items in stream:
                writer.writerows(items)
                count += len(items)
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

        md = await self._get_md(
            ctx=ctx,
            ancestor_selector=ancestor_selector,
            items_selector=items_selector,
            limit=10,
        )

        if not md:
            return None

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
                    content=md,
                ),
            ],
        )

        await ctx.send_debug_message(f"[{self.name}] Columns inference response: {res}")

        return callback(**res.model_dump())

    async def _get_md(
        self,
        ctx: Context,
        ancestor_selector: str,
        items_selector: str | None,
        limit: int = -1,
    ) -> str | None:
        # convert relative links to absolute links
        await self._process_relative_links()

        if items_selector is None:
            return await self._get_ancestor_md(ctx, ancestor_selector)
        else:
            return await self._get_items_md(ctx, items_selector, limit)

    async def _get_items_md(
        self,
        ctx: Context,
        items_selector: str,
        limit: int = -1,
    ) -> str | None:
        """
        Get the markdown content of the items to summarize

        Args:
            ctx: NPi context.
            items_selector: The selector of the items to summarize.
            limit: The maximum number of items to summarize.

        Returns:
            The markdown content of the items to summarize.
        """
        if limit == 0:
            return None

        unvisited_selector = items_selector + ":not([data-npi-visited])"

        # wait for the first unvisited item to be attached to the DOM
        try:
            await self.playwright.page.locator(unvisited_selector).first.wait_for(
                state="attached",
                timeout=30_000,
            )
        except TimeoutError:
            return None

        htmls = await self.playwright.page.evaluate(
            """
            ([unvisited_selector, limit]) => {
                const items = [...document.querySelectorAll(unvisited_selector)];
                const elems = limit === -1 ? items : items.slice(0, limit);
                
                return elems.map(elem => {
                    elem.setAttribute("data-npi-visited", "true");
                    return elem.outerHTML;
                });
            }
            """,
            [unvisited_selector, limit],
        )

        count = len(htmls)

        await ctx.send_debug_message(f"[{self.name}] Found {count} items to summarize")

        if count == 0:
            return None

        sections = [
            "<section>\n" + html_to_markdown(html) + "\n</section>" for html in htmls
        ]

        md = "\n".join(sections)

        await ctx.send_debug_message(f"[{self.name}] Items markdown: {md}")

        return md

    async def _get_ancestor_md(
        self,
        ctx: Context,
        ancestor_selector: str,
    ) -> str | None:
        """
        Get the markdown content of the ancestor element

        Args:
            ctx: NPi context.
            ancestor_selector: The selector of the ancestor element.

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
                htmls.append(await elem.inner_html())

        sections = [
            "<section>\n" + html_to_markdown(html) + "\n</section>" for html in htmls
        ]

        md = "\n".join(sections)

        await ctx.send_debug_message(f"[{self.name}] Ancestor additions: {md}")

        return md

    async def _llm_summarize(
        self,
        ctx: Context,
        md: str,
        output_columns: List[Column],
        scraping_type: ScrapingType,
    ) -> List[Dict[str, str]]:
        """
        Summarize the content of a webpage into a table using LLM.

        Args:
            ctx: NPi context.
            md: The markdown content to summarize.
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

        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=prompt.format(
                    column_defs=json.dumps(output_columns, ensure_ascii=False)
                ),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=md,
            ),
        ]

        final_response_content = ""

        while True:
            response = await ctx.llm.completion(
                messages=messages,
                max_tokens=4096,
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

        return list(csv.DictReader(final_response_content.splitlines()))

    async def _load_more(
        self,
        ctx: Context,
        ancestor_selector: str,
        items_selector: str | None,
        pagination_button_selector: str | None = None,
    ):
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
                "() => !!window.addedNodes?.length"
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
