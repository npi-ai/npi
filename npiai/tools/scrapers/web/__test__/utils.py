import json
from textwrap import indent
import time

from npiai.tools.scrapers.web import WebScraper
from npiai.tools.scrapers.page_analyzer import PageAnalyzer

# from npiai.utils.test_utils import DebugContext
from npiai import Context


async def auto_scrape(
    ctx: Context,
    url: str,
):
    async with PageAnalyzer(headless=False, force_captcha_detection=True) as analyzer:
        ancestor_selector = None
        items_selector = None

        print(f"Analyzing {url}:")
        step_start_time = time.monotonic()

        scraping_type = await analyzer.infer_scraping_type(
            ctx=ctx,
            url=url,
        )

        print(
            f"  - ({time.monotonic() - step_start_time:.2f}s) Inferred scraping type:",
            scraping_type,
        )

        if scraping_type == "list-like":
            step_start_time = time.monotonic()
            selectors = await analyzer.infer_similar_items_selector(ctx, url)

            print(
                f"  - ({time.monotonic() - step_start_time:.2f}s) Possible selectors:",
                indent(json.dumps(selectors, indent=2), prefix="    ").lstrip(),
            )

            if selectors:
                ancestor_selector = selectors["ancestor"]
                items_selector = selectors["items"]

        step_start_time = time.monotonic()

        infinite_scroll = await analyzer.support_infinite_scroll(
            ctx=ctx,
            url=url,
            items_selector=items_selector,
        )

        print(
            f"  - ({time.monotonic() - step_start_time:.2f}s) Support infinite scroll:",
            infinite_scroll,
        )

        step_start_time = time.monotonic()
        pagination_button_selector = await analyzer.get_pagination_button(
            ctx=ctx,
            url=url,
            items_selector=items_selector,
        )

        print(
            f"  - ({time.monotonic() - step_start_time:.2f}s) Pagination button:",
            pagination_button_selector,
        )

        scraper = WebScraper(
            headless=False,
            playwright=analyzer.playwright,
            url=url,
            scraping_type=scraping_type,
            ancestor_selector=ancestor_selector,
            items_selector=items_selector,
            pagination_button_selector=pagination_button_selector,
        )
        step_start_time = time.monotonic()
        columns = await scraper.infer_columns(
            ctx=ctx,
        )

        print(
            f"  - ({time.monotonic() - step_start_time:.2f}s) Inferred columns:",
            indent(json.dumps(columns, indent=2), prefix="   ").lstrip(),
        )

        stream = scraper.summarize_stream(
            ctx=ctx,
            output_columns=columns,
            limit=100,
            batch_size=5,
            concurrency=10,
        )

        start = time.monotonic()
        count = 0

        async for items in stream:
            print("Chunk:", json.dumps(items, indent=2, ensure_ascii=False))
            count += len(items["items"])

        end = time.monotonic()
        print(f"Summarized {count} items in {end - start:.2f} seconds")
