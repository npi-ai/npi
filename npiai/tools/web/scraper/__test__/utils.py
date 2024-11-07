import json
from textwrap import indent

from npiai.tools.web.scraper import Scraper
from npiai.tools.web.page_analyzer import PageAnalyzer

# from npiai.utils.test_utils import DebugContext
from npiai import Context


async def auto_scrape(
    ctx: Context,
    analyzer: PageAnalyzer,
    scraper: Scraper,
    url: str,
):
    ancestor_selector = None
    items_selector = None

    print(f"Analyzing {url}:")

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

        if selectors:
            ancestor_selector = selectors["ancestor"]
            items_selector = selectors["items"]

    infinite_scroll = await analyzer.support_infinite_scroll(
        url=url,
        items_selector=items_selector,
    )

    print("  - Support infinite scroll:", infinite_scroll)

    pagination_button_selector = await analyzer.get_pagination_button(
        ctx=ctx,
        url=url,
    )

    print("  - Pagination button:", pagination_button_selector)

    columns = await scraper.infer_columns(
        ctx=ctx,
        url=url,
        scraping_type=scraping_type,
        ancestor_selector=ancestor_selector,
        items_selector=items_selector,
    )

    print(
        "  - Inferred columns:",
        indent(json.dumps(columns, indent=2), prefix="   ").lstrip(),
    )

    stream = scraper.summarize_stream(
        ctx=ctx,
        url=url,
        scraping_type=scraping_type,
        ancestor_selector=ancestor_selector,
        items_selector=items_selector,
        pagination_button_selector=pagination_button_selector,
        output_columns=columns,
        limit=1 if scraping_type == "single" else 10,
    )

    async for items in stream:
        print("Chunk:", json.dumps(items, indent=2, ensure_ascii=False))
