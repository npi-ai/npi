import asyncio
import json
from textwrap import indent

from npiai.tools.scrapers.page_analyzer import PageAnalyzer
from npiai.tools.web.twitter import Twitter

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
    "https://github.com/facebook/react/issues/31207",
    "https://www.amazon.co.jp/product-reviews/B0BX2C4WYX/",
    "https://news.ycombinator.com/item?id=41853810",
    "https://x.com/home",
]


async def main():
    ctx = Context()

    # login with twitter
    async with Twitter(headless=False) as twitter:
        analyzer = PageAnalyzer(playwright=twitter.playwright)

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
                selectors = await analyzer.infer_similar_items_selector(ctx, url)

                print(
                    "  - Possible selectors:",
                    indent(json.dumps(selectors, indent=2), "    ").lstrip(),
                )

            print()


if __name__ == "__main__":
    asyncio.run(main())
