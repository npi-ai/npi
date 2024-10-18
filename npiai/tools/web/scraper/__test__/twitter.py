import asyncio
import json
from textwrap import indent

from npiai.tools.web.scraper import Scraper
from npiai.tools.web.page_analyzer import PageAnalyzer
from npiai.tools.web.twitter import Twitter

# from npiai.utils.test_utils import DebugContext
from npiai import Context

url = "https://x.com/home"


async def main():
    ctx = Context()

    async with Twitter(headless=False) as twitter:
        analyzer = PageAnalyzer(playwright=twitter.playwright)
        scraper = Scraper(batch_size=10, playwright=twitter.playwright)

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
                indent(json.dumps(selectors, indent=2), prefix="    ").lstrip(),
            )

        if not selectors:
            return

        columns = await scraper.infer_columns(
            ctx=ctx,
            url=url,
            ancestor_selector=selectors["ancestor"],
            items_selector=selectors["items"],
        )

        print(
            "  - Inferred columns:",
            indent(json.dumps(columns, indent=2), prefix="   ").lstrip(),
        )

        stream = scraper.summarize_stream(
            ctx=ctx,
            url=url,
            ancestor_selector=selectors["ancestor"],
            items_selector=selectors["items"],
            output_columns=columns,
            limit=10,
        )

        async for items in stream:
            print("Chunk:", json.dumps(items, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
