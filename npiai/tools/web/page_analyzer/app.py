import json
from textwrap import dedent

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)


from npiai import BrowserTool, function, Context
from npiai.utils import llm_tool_call


class PageAnalyzer(BrowserTool):
    name = "page_analyzer"
    description = "Analyze a web page for scraping purposes"
    system_prompt = dedent(
        """
        You are a web page analyzer that analyzes a web page for scraping purposes.
        """
    )

    async def _load_page(self, url: str):
        await self.playwright.page.goto(url)
        # wait for the page to become stable
        await self.playwright.page.wait_for_timeout(1000)

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

    @function
    async def support_infinite_scroll(self, url: str) -> bool:
        """
        Open the given URL and determine whether the page supports infinite scroll.

        Args:
            url: URL of the page
        """
        await self._load_page(url)

        return await self.playwright.page.evaluate(
            """
            () => {
                let mutateElementsCount = 0;
                const threshold = 10;
                
                const npiScrollObserver = new MutationObserver((records) => {
                    mutateElementsCount += records.length;
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
                     
                      const stepSize = pageHeight / 20;
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
                      }, 100);
                });
            }
            """,
        )

    @function
    async def get_pagination_button(self, ctx: Context, url: str) -> str | None:
        """
        Open the given URL and determine whether there is a pagination button. If there is, return the CSS selector of the pagination button. Otherwise, return None.

        Args:
            ctx: NPi Context
            url: URL of the page
        """
        await self._load_page(url)

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
                        3. Check if there is a pagination button on the page. Typically, a pagination button is a button or a link that allows users to navigate to the next page.
                        4. If you find a pagination button, call the tool with the ID of the element to retrieve the CSS selector. Otherwise, call the tool with -1 as the marker ID.
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

        return await self.get_selector_of_marker(res.marker_id)
