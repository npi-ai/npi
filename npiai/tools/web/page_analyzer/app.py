import json
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

_ScrapingType = Literal["list-like", "single"]


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

    async def _validate_pagination(self, ctx: Context, selector: str) -> bool:
        if not selector:
            return False

        handle = await self.playwright.page.evaluate_handle(
            "selector => document.querySelector(selector)",
            selector,
        )

        elem = handle.as_element()

        if not elem:
            return False

        await self.back_to_top()
        old_screenshot = await self.get_screenshot(full_page=True)
        old_url = await self.get_page_url()
        old_title = await self.get_page_title()

        await self.clear_bboxes()

        try:
            await self.click(elem)
        except PlaywrightError:
            return False

        await self.playwright.page.wait_for_timeout(3000)

        new_screenshot = await self.get_screenshot(full_page=True)
        new_url = await self.get_page_url()
        new_title = await self.get_page_title()

        def callback(is_next_page: bool):
            """
            Callback function to determine whether the pagination button is working.

            Args:
                is_next_page: A boolean value indicating whether the page is navigated to the next page or the content within pagination component is changed.
            """
            return is_next_page

        res = await llm_tool_call(
            llm=ctx.llm,
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

        return callback(**res.model_dump())

    @staticmethod
    async def set_scraping_type(scraping_type: _ScrapingType) -> _ScrapingType:
        """
        Set the inferrd scraping type of the page.

        Args:
            scraping_type: Inferred scraping type of the page. 'list-like' if the page contains a list of items, otherwise 'single'.
        """
        return scraping_type

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
        url: str,
        items_selector: str = None,
    ) -> bool:
        """
        Open the given URL and determine whether the page supports infinite scroll.

        Args:
            url: URL of the page
            items_selector: CSS selector of the items on the page
        """
        # use long wait time for pages to be fully loaded
        await self.load_page(url, wait=3000)

        return await self.playwright.page.evaluate(
            """
            (items_selector) => {
                let mutateElementsCount = 0;
                const threshold = items_selector === '*' ? 10 : 3;
                
                const npiScrollObserver = new MutationObserver((records) => {
                    for (const record of records) {
                        for (const node of record.addedNodes) {
                            if (node.nodeType === Node.ELEMENT_NODE && node.matches(items_selector)) {
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
                      
                      const interval = setInterval(() => {
                          current += stepSize;
                          window.scrollTo(0, current);
                          
                            if (current >= pageHeight || mutateElementsCount >= threshold) {
                                clearInterval(interval);
                                npiScrollObserver.disconnect();
                                
                                setTimeout(() => {
                                    resolve(mutateElementsCount >= threshold);
                                }, 1000);
                            }
                      }, 300);
                });
            }
            """,
            items_selector or "*",
        )

    @function
    async def get_pagination_button(self, ctx: Context, url: str) -> str | None:
        """
        Open the given URL and determine whether there is a pagination button. If there is, return the CSS selector of the pagination button. Otherwise, return None.

        Args:
            ctx: NPi Context
            url: URL of the page
        """
        await self.load_page(url)

        # use latest page url in case of redirections
        page_url = await self.get_page_url()
        page_title = await self.get_page_title()
        raw_screenshot = await self.get_screenshot(full_page=True)
        elements, _ = await self.get_interactive_elements(
            screenshot=raw_screenshot,
            full_page=True,
        )
        annotated_screenshot = await self.get_screenshot(full_page=True)

        res = await llm_tool_call(
            llm=ctx.llm,
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
                          attributes: Record<string, string>; // Some helpful attributes of the element
                          options?: string[]; // Available options of an <select> element. This property is only provided when the element is a <select> element.
                        }
                        
                        ## Instructions
                        
                        Follow the instructions to determine whether there is a pagination button on the current page for navigating to the next page:
                        1. Examine the screenshots, the URL, and the title of the page to understand the context, and then think about what the current page is.
                        2. Go through the elements array, pay attention to the `role`, `accessibleName`, and `accessibleDescription` properties to grab semantic information of the elements.
                        3. Check if there is a pagination button on the page. Typically, a pagination button is a button or a link that allows users to navigate to the next page. It usually contains text like "Next", "More", or "Load More".
                        4. If and only if you are confident that you have found a pagination button, call the tool with the ID of the element to retrieve the CSS selector. If you are not sure, or there is no pagination button, call the tool with -1. **Do not make any assumptions**.
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

        selector = await self.get_selector_of_marker(**res.model_dump())
        await ctx.send_debug_message(f"Pagination button selector: {selector}")

        is_working = await self._validate_pagination(ctx, selector)
        await ctx.send_debug_message(f"Pagination button is working: {is_working}")

        return selector if is_working else None

    @function
    async def infer_scraping_type(self, ctx: Context, url: str) -> _ScrapingType:
        """
        Infer the scraping type of the page. Returns 'list-like' if the page contains a list of items, otherwise 'single'.

        Args:
            ctx: NPi Context
            url: URL of the page
        """
        await self.load_page(url)
        page_url = await self.get_page_url()
        page_title = await self.get_page_title()
        screenshot = await self.get_screenshot(full_page=True)

        res = await llm_tool_call(
            llm=ctx.llm,
            tool=self.set_scraping_type,
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

        return await self.set_scraping_type(**res.model_dump())

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
        await self.load_page(url)

        # use latest page url in case of redirections
        page_url = await self.get_page_url()
        page_title = await self.get_page_title()
        raw_screenshot = await self.get_screenshot(full_page=True)

        contentful_elements = await self.playwright.page.evaluate(
            """
            (screenshot) => npi.getMostContentfulElements(screenshot)
            """,
            raw_screenshot,
        )

        annotated_screenshot = await self.get_screenshot(full_page=True)

        elements_as_markdown = []

        for el in contentful_elements:
            elements_as_markdown.append(
                {
                    "id": el["id"],
                    "content": html_to_markdown(el["html"]),
                }
            )

        res = await llm_tool_call(
            llm=ctx.llm,
            tool=self.compute_common_selectors,
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=dedent(
                        """
                        Analyze the given page and determine whether there are similar elements representing **the most meaningful** list of items. If there are, use the tool to calculate the common selector of the similar elements. 
                        
                        ## Provided Context
                        
                        - An annotated screenshot of the target page where the contextful elements are surrounded with rectangular bounding boxes in different colors. At the top left of each bounding box is a small rectangle in the same color as the bounding box. This is the label and it contains a number indicating the ID of that box. The label number starts from 0.
                        - The URL of the page.
                        - The title of the page.
                        - An array of the most contextful elements on the page. The elements are described as JSON objects defined in the Element Object section. Some irrelevant elements are filtered out.
                        
                        ## Element Object

                        The original HTML elements are described as the following JSON objects:
                        
                        type Element = {
                          id: string; // The Marker ID of the element
                          content: string; // The content of the element in Markdown format
                          groupId: string; // The ID of the group that the element belongs to
                        }
                        
                        ## Instructions
                        
                        Follow the instructions to determine whether there is a pagination button on the current page for navigating to the next page:
                        1. Examine the screenshot, the URL, and the title of the page to understand the context, and then think about what the current page is.
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

        return await self.compute_common_selectors(**res.model_dump())
