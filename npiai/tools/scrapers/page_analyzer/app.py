import json
from urllib.parse import urljoin
from textwrap import dedent
from typing import Literal, List
from typing_extensions import TypedDict
from playwright.async_api import Error as PlaywrightError


from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)


from npiai import BrowserTool, function, Context
from npiai.utils import llm_tool_call, html_to_markdown
from npiai.tools.scrapers.utils import init_items_observer, has_items_added

ScrapingType = Literal["list-like", "single"]

_MAX_SCREENSHOT_SIZE = (1280, 720)


class CommonSelectors(TypedDict):
    items: str
    ancestor: str
    anchors: str


class PageAnalyzer(BrowserTool):
    name = "page_analyzer"
    description = "Analyze a web page for scraping purposes"
    system_prompt = dedent(
        """
        You are a web page analyzer that analyzes a web page for scraping purposes.
        """
    )

    _force_captcha_detection: bool
    _open_new_page: bool

    def __init__(
        self,
        force_captcha_detection: bool = False,
        open_new_page=True,
        **kwargs,
    ):
        """
        Initialize the PageAnalyzer tool

        Args:
            force_captcha_detection: Whether to force the captcha detection when loading the page.
            open_new_page: Whether to open a new page when analyzing the page. If set to False, the current page will be used.
            **kwargs: BrowserTool arguments
        """
        super().__init__(**kwargs)
        self._force_captcha_detection = force_captcha_detection
        self._open_new_page = open_new_page

    async def _validate_pagination(
        self,
        ctx: Context,
        url: str,
        pagination_button_selector: str | None,
        items_selector: str | None = None,
    ) -> bool:
        if not pagination_button_selector:
            return False

        # validate the pagination button in a new playwright instance to avoid side effects
        playwright_clone = await self.playwright.clone()

        async with BrowserTool(playwright=playwright_clone) as browser:
            await browser.load_page(ctx, url)

            handle = await browser.playwright.page.evaluate_handle(
                "selector => document.querySelector(selector)",
                pagination_button_selector,
            )

            elem = handle.as_element()

            if not elem:
                return False

            await browser.back_to_top()
            old_screenshot = await browser.get_screenshot(
                full_page=True,
                max_size=_MAX_SCREENSHOT_SIZE,
            )
            old_url = await browser.get_page_url()
            old_title = await browser.get_page_title()

            await browser.clear_bboxes()

            try:
                await browser.click(elem)
            except PlaywrightError:
                return False

            has_items_selector = items_selector and items_selector != "*"

            # attach mutation observer to check if new items are added
            if has_items_selector:
                await init_items_observer(
                    playwright=browser.playwright,
                    ancestor_selector="body",
                    items_selector=items_selector,
                )

            try:
                await browser.playwright.page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=3000,
                )
            except TimeoutError:
                pass

            new_url = await browser.get_page_url()

            if new_url == old_url and has_items_selector:
                return await has_items_added(browser.playwright, timeout=5000)

            new_screenshot = await browser.get_screenshot(
                full_page=True,
                max_size=_MAX_SCREENSHOT_SIZE,
            )
            new_title = await browser.get_page_title()

            async def callback(is_next_page: bool):
                """
                Callback function to determine whether the pagination button is working.

                Args:
                    is_next_page: A boolean value indicating whether the page is navigated to the next page or the content within pagination component is changed.
                """
                return is_next_page

            return await llm_tool_call(
                ctx=ctx,
                tool=callback,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=dedent(
                            """
                            Compare the screenshots of the page before and after clicking the pagination button to determine whether the pagination button is working.
                            
                            ## Provided Context
                            - The URL of the page before clicking the pagination button.
                            - The title of the page before clicking the pagination button.
                            - The URL of the page after clicking the pagination button.
                            - The title of the page after clicking the pagination button.
                            - The screenshot of the page before clicking the pagination button.
                            - The screenshot of the page after clicking the pagination button.
                            
                            ## Instructions
                            
                            Follow the instructions to determine whether the pagination button is working:
                            1. Review the screenshot of the page before clicking the pagination button (the first screenshot) and think if the page actually supports pagination.
                            2. Compare the old URL and the new URL to see if the page is navigated to the next page.
                            3. Compare the old title and the new title to see the two pages are related.
                            4. Compare the first screenshot (the screenshot before clicking the pagination button) with the second screenshot (the screenshot after clicking the pagination button) to see if there are any differences. 
                            5. Check if previous page and the next page have the same structure but different content. If so, the pagination button is working. Note that opening or closing a popup/modal in the same page is not considered as pagination.
                            6. If the pagination button is working, call the tool with `true`. Otherwise, call the tool with `false`.
                            """
                        ),
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=[
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "old_url": old_url,
                                        "old_title": old_title,
                                        "new_url": new_url,
                                        "new_title": new_title,
                                    },
                                    ensure_ascii=False,
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": old_screenshot,
                                },
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": new_screenshot,
                                },
                            },
                        ],
                    ),
                ],
            )

    async def get_selector_of_marker(self, marker_id: int = -1) -> str | None:
        """
        Get the CSS selector of the element with the given marker ID. If the marker ID is -1, it means the marker is not found and None is returned.

        Args:
            marker_id: Marker ID of the element.
        """

        if marker_id == -1:
            return None

        return await self.playwright.page.evaluate(
            """(markerId) => {
                const el = npi.getElement(markerId);
                return el && npi.getUniqueSelector(el);
            }""",
            marker_id,
        )

    async def compute_common_selectors(
        self,
        anchor_ids: List[int],
    ) -> CommonSelectors | None:
        """
        Expand the anchors with the given IDs and compute the common items and ancestor selector.

        Args:
            anchor_ids: An array of IDs of the elements that are similar to each other and represent a meaningful list of items.
        """
        # print("anchor_ids:", anchor_ids)

        if not anchor_ids:
            return None

        # extract the first 3 elements
        # to find common items and ancestor selector
        return await self.playwright.page.evaluate(
            """(anchorIds) => {
                try {
                    const anchorElements = anchorIds.map(id => npi.getElement(id));
                                        
                    const selectors = npi.selectorUtils.getCommonItemsAndAncestor(...anchorElements);
                    
                    if (!selectors) {
                        return null;
                    }
                    
                    const splitSelectors = selectors.items.split(' ');
                    const lastSelector = splitSelectors.at(-1);
                    const isDirectChildrenSelector = splitSelectors.at(-2) === '>';
                    
                    if (!lastSelector) {
                        return null;
                    }
                                        
                    if (
                      !isDirectChildrenSelector &&
                      !lastSelector.startsWith('.') && 
                      !lastSelector.startsWith('[')
                    ) {
                      // avoid using tag name selector to select all descendants
                      return null;
                    }
                    
                    return {
                        ...selectors,
                        anchors: anchorElements.map(el => npi.getUniqueSelector(el)).join(', '),
                    }
                } catch {
                    return null;
                }
            }""",
            anchor_ids[:3],
        )

    @function
    async def support_infinite_scroll(
        self,
        ctx: Context,
        url: str,
        items_selector: str | None = None,
    ) -> bool:
        """
        Open the given URL and determine whether the page supports infinite scroll.

        Args:
            ctx: NPi Context
            url: URL of the page
            items_selector: CSS selector of the items on the page
        """
        if self._open_new_page:
            # use long wait time for pages to be fully loaded
            await self.load_page(
                ctx=ctx,
                url=url,
                timeout=3000,
                wait_for_selector=items_selector,
                force_capcha_detection=self._force_captcha_detection,
            )

        return await self.playwright.page.evaluate(
            """
            (items_selector) => {
                let mutateElementsCount = 0;
                const threshold = items_selector === '*' ? 10 : 3;
                const targetSelector = `${items_selector}, ${items_selector} *`;
                
                const npiScrollObserver = new MutationObserver((records) => {
                    for (const record of records) {
                        for (const node of record.addedNodes) {
                            if (node.nodeType === Node.ELEMENT_NODE && node.matches(targetSelector)) {
                                mutateElementsCount++;
                            }
                        }
                    }
                });
                
                npiScrollObserver.observe(
                    document.body, 
                    { childList: true, subtree: true }
                );
                
                return new Promise((resolve) => {
                    function done() {
                        npiScrollObserver.disconnect();
                        resolve(mutateElementsCount >= threshold);
                    }
                    
                    const body = document.body;
                    const html = document.documentElement;
                
                    const pageHeight = Math.max(
                        body.scrollHeight,
                        body.offsetHeight,
                        html.clientHeight,
                        html.scrollHeight,
                        html.offsetHeight,
                    );
                    
                    const stepSize = pageHeight / 10;
                    let current = 0;
                    
                    if (items_selector !== '*') {
                      const lastItem = [...document.querySelectorAll(items_selector)].at(-1);
                      
                      if (lastItem) {
                          current = lastItem.getBoundingClientRect().top;
                          window.scrollTo(0, current);
                      }
                    }
                    
                    const interval = setInterval(() => {
                        current += stepSize;
                        window.scrollTo(0, current);
                        
                        if (current >= pageHeight || mutateElementsCount >= threshold) {
                            clearInterval(interval);
                            
                            if (mutateElementsCount >= threshold) {
                                done();
                            } else {
                                setTimeout(done, 300);
                            }
                        }
                    }, 300);
                });
            }
            """,
            items_selector or "*",
        )

    @function
    async def get_pagination_button(
        self,
        ctx: Context,
        url: str,
        items_selector: str | None = None,
    ) -> str | None:
        """
        Open the given URL and determine whether there is a pagination button. If there is, return the CSS selector of the pagination button. Otherwise, return None.

        Args:
            ctx: NPi Context
            url: URL of the page
            items_selector: CSS selector of the items on the page
        """
        if self._open_new_page:
            await self.load_page(
                ctx,
                url,
                force_capcha_detection=self._force_captcha_detection,
            )

        # use latest page url in case of redirections
        page_url = await self.get_page_url()
        page_title = await self.get_page_title()
        raw_screenshot = await self.get_screenshot(
            full_page=True,
            max_size=(128, 72),  # raw screenshot is only used to mark elements
        )
        elements, _ = await self.get_interactive_elements(
            screenshot=raw_screenshot,
            full_page=True,
        )
        annotated_screenshot = await self.get_screenshot(
            full_page=True,
            max_size=_MAX_SCREENSHOT_SIZE,
        )

        # remove unnecessary properties
        for el in elements:
            attrs = el.pop("attributes", None)
            el.pop("options", None)

            if attrs and "href" in attrs:
                el["href"] = urljoin(page_url, attrs["href"])

        pagination_button_selector = await llm_tool_call(
            ctx=ctx,
            tool=self.get_selector_of_marker,
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=dedent(
                        """
                        Analyze the given page and determine whether there is a pagination button that allows users to **navigate to the next page**. If there is, use the tool to retrieve the CSS selector of the pagination button.
                        
                        ## Provided Context
                        
                        - An annotated screenshot of the target page where the interactive elements are surrounded with rectangular bounding boxes in different colors. At the top left of each bounding box is a small rectangle in the same color as the bounding box. This is the label and it contains a number indicating the ID of that box. The label number starts from 0.
                        - The URL of the page.
                        - The title of the page.
                        - An array of the interactive elements on the page. The elements are described as JSON objects defined in the Element Object section.
                        
                        ## Element Object

                        The original HTML elements are described as the following JSON objects:
                        
                        type Element = {
                          id: string; // The Marker ID of the element
                          tag: string; // The tag of the element
                          role: string | null; // The WAI-ARIA accessible role of the element
                          accessibleName: string; // The WAI-ARIA accessible name of the element
                          accessibleDescription: string; // The WAI-ARIA accessible description of the element
                          href?: string; // The href attribute of the element if it is a link
                        }
                        
                        ## Instructions
                        
                        Follow the instructions to determine whether there is a pagination button on the current page for navigating to the next page:
                        1. Examine the screenshots, the URL, and the title of the page to understand the context, and then think about what the current page is.
                        2. Go through the elements array, pay attention to the `role`, `accessibleName`, and `accessibleDescription` properties to grab semantic information of the elements.
                        3. Check if there is a pagination button on the page. Typically, a pagination button is a button or a link that allows users to navigate to the next page. It usually contains text like "Next" or "Load More".
                        4. Links pointing to the same url as the current page are not considered as pagination buttons.
                        5. If and only if you are confident that you have found a pagination button, call the tool with the ID of the element to retrieve the CSS selector. If you are not sure, or there is no pagination button, call the tool with -1. **Do not make any assumptions**.
                        """
                    ),
                ),
                ChatCompletionUserMessageParam(
                    role="user",
                    content=[
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "url": page_url,
                                    "title": page_title,
                                    "elements": elements,
                                },
                                ensure_ascii=False,
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": annotated_screenshot,
                            },
                        },
                    ],
                ),
            ],
        )

        await ctx.send_debug_message(
            f"Pagination button selector: {pagination_button_selector}"
        )

        is_working = await self._validate_pagination(
            ctx=ctx,
            url=url,
            pagination_button_selector=pagination_button_selector,
            items_selector=items_selector,
        )
        await ctx.send_debug_message(f"Pagination button is working: {is_working}")

        return pagination_button_selector if is_working else None

    @function
    async def infer_scraping_type(self, ctx: Context, url: str) -> ScrapingType:
        """
        Infer the scraping type of the page. Returns 'list-like' if the page contains a list of items, otherwise 'single'.

        Args:
            ctx: NPi Context
            url: URL of the page
        """
        if self._open_new_page:
            await self.load_page(
                ctx,
                url,
                force_capcha_detection=self._force_captcha_detection,
            )

        page_url = await self.get_page_url()
        page_title = await self.get_page_title()
        screenshot = await self.get_screenshot(
            full_page=True,
            max_size=_MAX_SCREENSHOT_SIZE,
        )

        async def callback(scraping_type: ScrapingType):
            """
            Set the inferrd scraping type of the page.

            Args:
                scraping_type: Inferred scraping type of the page. 'list-like' if the page contains a list of items, otherwise 'single'.
            """
            return scraping_type

        return await llm_tool_call(
            ctx=ctx,
            tool=callback,
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=dedent(
                        """
                        Analyze the given page and determine the scraping type of the page. The scraping type is 'list-like' if the page contains a list of similar items, otherwise 'single'.
                        
                        ## Provided Context
                        
                        - A screenshot of the target page.
                        - The URL of the page.
                        - The title of the page.
                        
                        ## Instructions
                        
                        Follow the instructions to determine the scraping type of the page:
                        1. Examine the screenshot to understand the context of the page.
                        2. Determine whether the page contains a list of similar items or not. Typically, a list-like page contains multiple items with similar structures, such as search results or product listings.
                        3. If the page contains a list of similar items, call the tool with 'list-like'. Otherwise, call the tool with 'single'.
                        """
                    ),
                ),
                ChatCompletionUserMessageParam(
                    role="user",
                    content=[
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "url": page_url,
                                    "title": page_title,
                                },
                                ensure_ascii=False,
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": screenshot,
                            },
                        },
                    ],
                ),
            ],
        )

    @function
    async def infer_similar_items_selector(
        self,
        ctx: Context,
        url: str,
    ) -> CommonSelectors | None:
        """
        Open the given URL and determine whether there are similar elements representing a meaningful list of items. If there are, return the common selector of the similar elements, the ancestor selector, and the selectors of the anchor elements. Otherwise, return None.

        Args:
            ctx: NPi Context
            url: URL of the page
        """
        if self._open_new_page:
            await self.load_page(
                ctx,
                url,
                timeout=3000,
                force_capcha_detection=self._force_captcha_detection,
            )

        # use latest page url in case of redirections
        page_url = await self.get_page_url()
        page_title = await self.get_page_title()
        raw_screenshot = await self.get_screenshot(full_page=True)

        contentful_elements = await self.playwright.page.evaluate(
            """
            (screenshot) => npi.getMostContentfulElements(screenshot, 5)
            """,
            raw_screenshot,
        )

        annotated_screenshot = await self.get_screenshot(full_page=True)

        elements_as_markdown = []
        group_element_count = {}

        for el in contentful_elements:
            group_id = el["groupId"]

            if group_id not in group_element_count:
                group_element_count[group_id] = 0

            # only take the 3 examples from each group to reduce token usage
            # and improve response time
            if group_element_count[group_id] > 3:
                continue

            group_element_count[group_id] += 1

            elements_as_markdown.append(
                {
                    "id": el["id"],
                    "groupId": group_id,
                    "content": html_to_markdown(el["html"]),
                }
            )

        return await llm_tool_call(
            ctx=ctx,
            tool=self.compute_common_selectors,
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=dedent(
                        """
                        Analyze the given page and determine whether there are similar elements representing **the most meaningful** list of items. If there are, use the tool to calculate the common selector of the similar elements. 
                        
                        ## Provided Context
                        
                        - The URL of the page.
                        - The title of the page.
                        - An array of the most contextful elements on the page. The elements are described as JSON objects defined in the Element Object section. Some irrelevant elements are filtered out.
                        - An annotated screenshot of the target page where the most contextful elements are surrounded with rectangular bounding boxes in different colors. At the top left of each bounding box is a small rectangle in the same color as the bounding box. This is the label and it contains a number indicating the ID of that box. The label number starts from 0.
                        
                        ## Element Object

                        The original HTML elements are described as the following JSON objects:
                        
                        type Element = {
                          id: string; // The Marker ID of the element
                          content: string; // The content of the element in Markdown format
                          groupId: string; // The ID of the group that the element belongs to
                        }
                        
                        ## Instructions
                        
                        Follow the instructions to determine whether there are similar elements representing the most meaningful list of items:
                        1. Examine the URL, and the title of the page to understand the context, and then think about what the current page is.
                        2. Go through the elements array, grab the semantic information of the elements via the "content" property. Pay attention to the elements with the same group ID as they are under the same parent element.
                        3. Check if there are similar elements representing **the most meaningful list** of items. Typically, these elements link to the detail pages of the items. Note that these elements should not be the pagination buttons and should contain enough meaningful information, not just some short phrases.
                        4. If you find meaningful similar elements, call the tool with a list of the IDs of the elements to compute the common selectors. Otherwise, call the tool with an empty list.
                        """
                    ),
                ),
                ChatCompletionUserMessageParam(
                    role="user",
                    content=[
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "url": page_url,
                                    "title": page_title,
                                    "elements": elements_as_markdown,
                                },
                                ensure_ascii=False,
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": annotated_screenshot,
                            },
                        },
                    ],
                ),
            ],
        )
