import csv
import re
import json
import os
from typing import List, Dict
from typing_extensions import TypedDict, Annotated
from textwrap import dedent

from markdownify import MarkdownConverter
from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from npiai import function, BrowserTool, Context
from npiai.core import NavigatorAgent
from npiai.utils import is_cloud_env, llm_tool_call


class Column(TypedDict):
    name: Annotated[str, "Name of the column"]
    description: Annotated[str | None, "Brief description of the column"]


class NonBase64ImageConverter(MarkdownConverter):
    def convert_img(self, el, text, convert_as_inline):
        src = el.attrs.get("src", "")
        if src.startswith("data:image"):
            el.attrs["src"] = "<base64_image>"
        return super().convert_img(el, text, convert_as_inline)

    # def convert_div(self, el, text, convert_as_inline):
    #     if convert_as_inline or not text:
    #         return text
    #
    #     return f"{text}\n\n"


def html_to_markdown(html: str, **options) -> str:
    return NonBase64ImageConverter(**options).convert(html).strip()


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

    def __init__(self, headless: bool = True, batch_size: int = 10):
        super().__init__(
            headless=headless,
        )
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

    @function
    async def summarize(
        self,
        ctx: Context,
        url: str,
        output_columns: List[Column],
        ancestor_selector: str | None = None,
        items_selector: str | None = None,
        pagination_button_selector: str | None = None,
        output_file: str | None = None,
        limit: int = -1,
    ) -> str:
        """
        Summarize the content of a webpage into a table (JSON format).

        Args:
            ctx: NPi context.
            url: The URL to open.
            output_columns: The columns of the output table. If not provided, use the `infer_columns` function to infer the columns.
            ancestor_selector: The selector of the ancestor element containing the items to summarize. If None, the 'body' element is used.
            items_selector: The selector of the items to summarize. If None, all the children of the ancestor element are used.
            pagination_button_selector: The selector of the pagination button (e.g., the "Next Page" button) to load more items. Used when the items are paginated. By default, the tool will scroll to load more items.
            output_file: The file path to save the output. If None, the output is saved to 'scraper_output.json'.
            limit: The maximum number of items to summarize. If -1, all items are summarized.
        """
        if limit == 0:
            return "No items to summarize"

        await self.playwright.page.goto(url)

        if not ancestor_selector:
            ancestor_selector = "body"

        if not output_file:
            output_file = "scraper_output.json"

        results = []

        while True:
            remaining = (
                min(self._batch_size, limit - len(results)) if limit != -1 else -1
            )

            md = await self._get_md(
                ctx=ctx,
                ancestor_selector=ancestor_selector,
                items_selector=items_selector,
                limit=remaining,
            )

            if not md:
                break

            items = await self._llm_summarize(ctx, md, output_columns)

            await ctx.send_debug_message(f"[{self.name}] Summarized {len(items)} items")

            if not items:
                break

            results.extend(items)

            await ctx.send_debug_message(
                f"[{self.name}] Summarized {len(results)} items in total"
            )

            if limit != -1 and len(results) >= limit:
                break

            await self._load_more(
                ctx,
                ancestor_selector,
                items_selector,
                pagination_button_selector,
            )

        final_results = results[:limit] if limit != -1 else results

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, "w") as f:
            f.write(json.dumps(final_results, indent=4, ensure_ascii=False))

        return f"Saved {len(final_results)} items to {output_file}"

    @function
    async def infer_columns(
        self,
        ctx: Context,
        url: str,
        ancestor_selector: str | None,
        items_selector: str | None,
    ) -> List[Column] | None:
        """
        Infer the columns of the output table by finding the common nature of the items to summarize.

        Args:
            ctx: NPi context.
            url: The URL to open.
            ancestor_selector: The selector of the ancestor element containing the items to summarize. If None, the 'body' element is used.
            items_selector: The selector of the items to summarize. If None, all the children of the ancestor element are used.
        """

        await self.playwright.page.goto(url)

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
                columns: The inferred columns. Each column is a dictionary with 'name' and 'description' keys, where 'description' is optional.
            """
            return columns

        res = await llm_tool_call(
            llm=ctx.llm,
            tool=callback,
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=dedent(
                        """
                        Imagine you are summarizing the content of a webpage into a table. Find the common nature of the provided items and suggest the columns for the output table.
                        """
                    ),
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
        if items_selector is None:
            return await self._get_ancestor_md(ctx, ancestor_selector, limit)
        else:
            return await self._get_items_md(ctx, items_selector, limit)

    async def _get_items_md(
        self,
        ctx: Context,
        items_selector: str,
        limit: int = -1,
    ) -> str | None:
        if limit == 0:
            return None

        unvisited_selector = items_selector + ":not([data-npi-visited])"

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
        limit: int = -1,
    ) -> str | None:
        if limit == 0:
            return None

        # check if there are mutation records
        htmls = await self.playwright.page.evaluate(
            """
            (limit) => {
                const { addedNodes } = window;
                
                if (addedNodes?.length) {
                    const nodes = limit === -1 ? addedNodes : addedNodes.slice(0, limit);
                    window.addedNodes = [];
                    
                    return nodes.map(node => {
                        node.setAttribute("data-npi-visited", "true");
                        return node.outerHTML;
                    });
                }
                
                return null;
            }
            """,
            limit,
        )

        if htmls is None:
            locator = self.playwright.page.locator(ancestor_selector)

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
    ) -> List[Dict[str, str]]:
        column_defs = ""

        for column in output_columns:
            column_defs += (
                f"{column['name']}: {column['description'] or 'No description'}\n"
            )

        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=dedent(
                    f"""
                    You are a web scraper agent helping user summarize the content of a webpage into a table.
                    For the given markdown content, summarize the content into a table with the following columns:
                    
                    # Column Definitions
                    {column_defs}
                    
                    # Response Format
                    Respond with the table in CSV format. Each column value should be enclosed in double quotes and separated by commas.
                    """
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
