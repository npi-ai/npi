import asyncio
import json
from textwrap import indent

from npiai.tools.web.page_analyzer import PageAnalyzer

# from npiai.utils.test_utils import DebugContext
from npiai import Context

urls = [
    "https://www.bardeen.ai/playbooks",
    "https://www.bardeen.ai/playbooks/get-data-from-the-currently-opened-imdb-com-title-page",
    "https://ifttt.com/explore",
    "https://retool.com/templates",
    "https://www.google.com/search?q=test&hl=ja",
    "https://www.amazon.com/s?k=test",
    "https://github.com/facebook/react/issues",
]


async def main():
    ctx = Context()
    async with PageAnalyzer(headless=False) as analyzer:
        for url in urls:
            print(f"Analyzing {url}:")

            infinite_scroll = await analyzer.support_infinite_scroll(
                url=url,
            )

            print("  - Support infinite scroll:", infinite_scroll)

            pagination = await analyzer.get_pagination_button(
                ctx=ctx,
                url=url,
            )

            print("  - Pagination button:", pagination)

            scraping_type = await analyzer.infer_scraping_type(
                ctx=ctx,
                url=url,
            )

            print("  - Inferred scraping type:", scraping_type)

            if scraping_type == "list-like":
                anchors = await analyzer.get_similar_items(ctx, url)

                print(
                    "  - Possible selectors:",
                    indent(json.dumps(anchors, indent=2), "    ").lstrip(),
                )

            print()


if __name__ == "__main__":
    asyncio.run(main())
