import csv
import re
import json
from typing import List, Dict
from textwrap import dedent

from markdownify import MarkdownConverter
from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from npiai import function, BrowserTool, Context
from npiai.core import NavigatorAgent
from npiai.utils import is_cloud_env, parse_json_response


class NonBase64ImageConverter(MarkdownConverter):
    def convert_img(self, el, text, convert_as_inline):
        src = el.attrs.get("src", "")
        if src.startswith("data:image"):
            el.attrs["src"] = "<base64_image>"
        return super().convert_img(el, text, convert_as_inline)

    def convert_div(self, el, text, convert_as_inline):
        if convert_as_inline or not text:
            return text

        return f"{text}\n\n"


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

    _last_ancestor_md: str | None
    _navigator: NavigatorAgent

    def __init__(self, headless: bool = True):
        super().__init__(
            headless=headless,
        )
        self._last_ancestor_md = None
        self._navigator = NavigatorAgent(
            playwright=self.playwright,
        )
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
        ancestor_selector: str | None = None,
        items_selector: str | None = None,
        output_columns: List[str] | None = None,
        limit: int = -1,
    ) -> str:
        """
        Summarize the content of a webpage into a table (JSON format).

        Args:
            ctx: NPi context.
            url: The URL to open.
            ancestor_selector: The selector of the ancestor element containing the items to summarize. If None, the 'body' element is used.
            items_selector: The selector of the items to summarize. If None, all the children of the ancestor element are used.
            output_columns: The columns of the output table. If None, they are automatically generated.
            limit: The maximum number of items to summarize. If -1, all items are summarized.
        """
        if limit == 0:
            return "No items to summarize"

        await self.playwright.page.goto(url)

        if ancestor_selector is None:
            ancestor_selector = "body"

        if items_selector is None:

            async def get_md():
                return await self._get_ancestor_md(ctx, ancestor_selector)

        else:

            async def get_md():
                return await self._get_items_md(ctx, items_selector)

        if output_columns is None:
            md = await get_md()
            output_columns = await self._infer_columns(ctx, md)

        results = []

        while True:
            md = await get_md()

            if md is None:
                break

            items = await self._llm_summarize(ctx, md, output_columns)

            await ctx.send_debug_message(f"[{self.name}] Summarized {len(items)} items")

            if not items:
                break

            results.extend(items)

            if limit != -1 and len(results) >= limit:
                break

            await self._load_more(ctx, ancestor_selector)

        final_results = results[:limit] if limit != -1 else results

        with open("scraper_output.json", "w") as f:
            f.write(json.dumps(final_results, indent=4, ensure_ascii=False))

        return f"Saved {len(final_results)} items to scraper_output.json"

    async def _get_items_md(self, ctx: Context, items_selector: str) -> str | None:
        locator = self.playwright.page.locator(
            items_selector + ":not([data-npi-visited])"
        )

        count = await locator.count()

        await ctx.send_debug_message(f"[{self.name}] Found {count} items to summarize")

        if count == 0:
            return None

        sections = []

        for elem in await locator.all():
            sections.append(await elem.inner_html())

        md = html_to_markdown("\n".join(sections))

        await ctx.send_debug_message(f"[{self.name}] Items markdown: {md}")

        await locator.evaluate_all(
            'elems => elems.forEach(el => el.setAttribute("data-npi-visited", "true"))'
        )

        return md

    async def _get_ancestor_md(
        self,
        ctx: Context,
        ancestor_selector: str,
    ) -> str | None:
        # check if there are mutation records
        html = await self.playwright.page.evaluate(
            """
            () => {
                const { addedNodes } = window;
                
                if (addedNodes?.length) {
                    window.addedNodes = [];
                    return addedNodes.map(node => node.outerHTML).join("\\n");
                }
                
                return null;
            }
            """
        )

        if html is None:
            locator = self.playwright.page.locator(ancestor_selector)

            if not await locator.count():
                return None

            sections = []

            for elem in await locator.all():
                sections.append(await elem.inner_html())

            html = "\n".join(sections)

        md = html_to_markdown(html)

        await ctx.send_debug_message(f"[{self.name}] Ancestor additions: {md}")

        return md

    async def _llm_summarize(
        self,
        ctx: Context,
        md: str,
        output_columns: List[str],
    ) -> List[Dict[str, str]]:
        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=dedent(
                    f"""
                    You are a web scraper agent helping user summarize the content of a webpage into a table.
                    For the given markdown content, summarize the content into a table with the following columns: {json.dumps(output_columns, ensure_ascii=False)}.
                    Respond with the table in CSV format.
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

    async def _infer_columns(self, ctx: Context, md: str) -> List[str]:
        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=dedent(
                    """
                    Imagine you are summarizing the content of a webpage into a table. Find the common nature of the provided items and suggest the columns for the output table. Respond with the columns in a list format: ['column1', 'column2', ...]
                    """
                ),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=md,
            ),
        ]

        response = await ctx.llm.completion(
            messages=messages,
            max_tokens=4096,
        )
        content = response.choices[0].message.content

        await ctx.send_debug_message(
            f"[{self.name}] Columns inference response: {content}"
        )

        return parse_json_response(content)

    async def _load_more(self, ctx: Context, ancestor_selector: str):
        # attach mutation observer to the ancestor element
        await self.playwright.page.evaluate(
            """
            () => {
                window.addedNodes = [];
                window.npiObserver = new MutationObserver((records) => {
                    for (const record of records) {
                        for (const addedNode of record.addedNodes) {
                            window.addedNodes.push(addedNode);
                        }
                    }
                });
            }
            """
        )

        await self.playwright.page.evaluate(
            f"""
            () => {{
                window.npiObserver.observe(
                    document.querySelector("{ancestor_selector}"), 
                    {{ childList: true, subtree: true }}
                );
            }}
            """
        )

        # check if the page is scrollable
        # if so, scroll to load more items
        if await self.is_scrollable():
            locator = self.playwright.page.locator(ancestor_selector)
            await locator.evaluate("el => el.scrollIntoView({block: 'end'})")
            await ctx.send_debug_message(f"[{self.name}] Scrolled to load more items")
        else:
            # otherwise, check if there is a pagination element
            # if so, navigate to the next page using navigator
            await self.back_to_top()
            await self._navigator.chat(
                ctx=ctx,
                # TODO: optimize the instruction
                instruction="Check if there is a pagination element on the page. If so, navigate to the next page.",
            )
            await ctx.send_debug_message(f"[{self.name}] Navigated to the next page")

        await self.playwright.page.wait_for_timeout(3000)

        # clear the mutation observer
        await self.playwright.page.evaluate(
            "() => { window.npiObserver.disconnect(); }"
        )
