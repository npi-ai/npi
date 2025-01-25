import asyncio
import hashlib
import re
from textwrap import dedent
from typing import List, Set, Literal

from markdownify import MarkdownConverter
from playwright.async_api import TimeoutError

from npiai import BrowserTool, Context
from npiai.core import PlaywrightContext
from npiai.tools.scrapers import BaseScraper, SourceItem
from npiai.tools.scrapers.utils import init_items_observer, has_items_added
from npiai.utils import CompactMarkdownConverter

ScrapingType = Literal["single", "list-like"]


class WebScraper(BaseScraper, BrowserTool):
    name = "web-scraper"
    description = (
        "A web scraper agent that can summarize the content of a webpage into a table"
    )
    system_prompt = dedent(
        """
        You are a general web scraper agent helping user summarize the content of a webpage into a table.
        """
    )

    markdown_converter: MarkdownConverter = CompactMarkdownConverter()

    url: str
    scraping_type: ScrapingType
    ancestor_selector: str
    items_selector: str | None
    pagination_button_selector: str | None
    skip_item_hashes: Set[str] | None

    # The maximum number of items to summarize in a single batch
    _batch_size: int

    # all items loaded flag
    _all_items_loaded: bool = False

    # asyncio lock to prevent concurrent access to the webpage
    # to avoid retrieving the same items multiple times
    _webpage_access_lock: asyncio.Lock

    # The list of hashes of items that have been skipped
    _matched_hashes: List[str]

    def __init__(
        self,
        url: str,
        scraping_type: ScrapingType,
        ancestor_selector: str | None = None,
        items_selector: str | None = None,
        pagination_button_selector: str | None = None,
        skip_item_hashes: List[str] | None = None,
        headless: bool = True,
        playwright: PlaywrightContext = None,
    ):
        BaseScraper.__init__(self)
        BrowserTool.__init__(self, headless=headless, playwright=playwright)
        self.url = url
        self.scraping_type = scraping_type
        self.ancestor_selector = ancestor_selector or "body"
        self.items_selector = items_selector
        self.pagination_button_selector = pagination_button_selector
        self.skip_item_hashes = set(skip_item_hashes) if skip_item_hashes else None
        self._matched_hashes = []
        self._webpage_access_lock = asyncio.Lock()

    def get_matched_hashes(self) -> List[str]:
        return self._matched_hashes

    async def init_data(self, ctx: Context):
        self._matched_hashes = []
        await self.load_page(
            ctx=ctx,
            url=self.url,
            timeout=3000,
            wait_for_selector=self.items_selector,
        )

    async def next_items(
        self,
        ctx: Context,
        count: int,
    ) -> List[SourceItem] | None:
        async with self._webpage_access_lock:
            if self._all_items_loaded:
                return None

            await self._load_more(ctx)

            # convert relative links to absolute links
            await self._process_relative_links()

            if self.items_selector is None:
                res = await self._convert_ancestor()
            else:
                res = await self._convert_items(count)

            if not res:
                # if no items are found, check if there are any captcha
                await self.detect_captcha(ctx)
                self._all_items_loaded = True

            return res

    async def _convert_items(
        self,
        limit: int = -1,
    ) -> List[SourceItem] | None:
        """
        Get the markdown content of the items to summarize

        Args:
            limit: The maximum number of items to summarize.

        Returns:
            The markdown content of the items to summarize.
        """
        if limit == 0:
            return None

        locator = self.playwright.page.locator(
            self.items_selector + ":not([data-npi-visited])"
        )

        # wait for the first unvisited item to be attached to the DOM
        try:
            await locator.first.wait_for(
                state="attached",
                timeout=3_000,
            )
        except TimeoutError:
            return None

        results: List[SourceItem] = []

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

            if self.skip_item_hashes and md5 in self.skip_item_hashes:
                self._matched_hashes.append(md5)
                continue

            results.append(
                SourceItem(
                    hash=md5,
                    data=markdown,
                )
            )

            if len(results) >= limit:
                break

        return results

    async def _convert_ancestor(
        self,
    ) -> List[SourceItem] | None:
        """
        Get the markdown content of the ancestor element

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
            locator = self.playwright.page.locator(
                self.ancestor_selector + ":not([data-npi-visited])"
            )

            # wait for the ancestor element to be attached to the DOM
            try:
                await locator.first.wait_for(state="attached", timeout=3_000)
            except TimeoutError:
                return None

            if not await locator.count():
                return None

            htmls = []

            # use all ancestors here to avoid missing any items
            for elem in await locator.all():
                htmls.append(
                    await elem.evaluate(
                        """
                        elem => {
                            elem.setAttribute('data-npi-visited', 'true');
                            return elem.outerHTML;
                        }
                        """
                    )
                )

        results: List[SourceItem] = []

        for html in htmls:
            markdown, md5 = self._html_to_md_and_hash(html)

            if self.skip_item_hashes and md5 in self.skip_item_hashes:
                self._matched_hashes.append(md5)
                continue

            results.append(
                SourceItem(
                    hash=md5,
                    data=markdown,
                )
            )

        return results

    def _html_to_md_and_hash(self, html: str):
        markdown = re.sub(r"\n+", "\n", self.markdown_converter.convert(html)).strip()
        md5 = hashlib.md5(markdown.encode()).hexdigest()
        return markdown, md5

    async def _load_more(
        self,
        ctx: Context,
    ):
        unvisited_items_selector = (
            self.items_selector or "*"
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
        await init_items_observer(
            playwright=self.playwright,
            ancestor_selector=self.ancestor_selector,
            items_selector=self.items_selector,
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
                self.ancestor_selector,
            )
            await ctx.send_debug_message(f"[{self.name}] Scrolled to load more items")
            more_content_loaded = await has_items_added(self.playwright, timeout=3000)

        if not more_content_loaded and self.pagination_button_selector:
            handle = await self.playwright.page.evaluate_handle(
                "selector => document.querySelector(selector)",
                self.pagination_button_selector,
            )

            elem = handle.as_element()

            if not elem:
                await ctx.send_debug_message(
                    f"[{self.name}] Pagination button not found"
                )
                return

            await self.click(elem)
            await ctx.send_debug_message(f"[{self.name}] Clicked pagination button")
            try:
                await self.playwright.page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=3000,
                )
            except TimeoutError:
                pass

        # clear the mutation observer
        await self.playwright.page.evaluate(
            "() => { window.npiObserver?.disconnect(); }"
        )

    async def _process_relative_links(self):
        await self.playwright.page.evaluate(
            """
            () => {
                if (window.npiProcessedRelativeLinks) {
                    return;
                }
                
                function process(root) {
                    const elements = [...root.querySelectorAll('a[href]')];
                    
                    if (root.matches('a[href]')) {
                        elements.push(root);
                    }
                    
                    elements.forEach(a => {
                        const href = a.getAttribute('href');
                        
                        if (!href) {
                            return;
                        }
                        
                        const url = new URL(href, window.location.href);
                        a.setAttribute('href', url.href);
                    });
                }
                
                process(document.body);
                
                const observer = new MutationObserver((records) => {
                    for (const record of records) {
                        for (const node of record.addedNodes) {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                process(node);
                            }
                        }
                    }
                });
                
                observer.observe(document.body, { childList: true, subtree: true });
                
                window.npiProcessedRelativeLinks = true;
            }
            """
        )
