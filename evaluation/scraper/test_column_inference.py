import json
import os
from textwrap import dedent
import pytest

from npiai.tools.scrapers.web import WebScraper
from npiai.tools.web.twitter import Twitter, TwitterClient
from npiai.context import Context
from npiai.evaluation import llm_assert


def get_columns(columns):
    return [
        {
            "column": column["name"],
            "description": column["description"],
        }
        for column in columns
    ]


@pytest.mark.repeat(5)
async def test_twitter_columns():
    ctx = Context()
    client = TwitterClient(
        ctx=ctx,
        username=os.environ["TWITTER_USERNAME"],
        password=os.environ["TWITTER_PASSWORD"],
    )
    async with Twitter(client=client) as twitter:
        scraper = WebScraper(
            url="https://x.com/home",
            playwright=twitter.playwright,
            scraping_type="list-like",
            ancestor_selector=".r-f8sm7e:nth-child(5) > .css-175oi2r > .css-175oi2r > div",
            items_selector=".r-f8sm7e:nth-child(5) > .css-175oi2r > .css-175oi2r > div > .css-175oi2r",
        )

        res = await scraper.infer_columns(
            ctx=ctx,
        )

        columns = get_columns(res)

        await llm_assert(
            ctx=ctx,
            output=json.dumps(columns),
            expectations=dedent(
                f"""
                The agent should output a list of dictionaries representing the columns of a table. The table should include the following information:
                
                - The username of the user who posted the content.
                - The main content of the post.
                - The URL of the post.
                """,
            ),
            constraints=dedent(
                """
                - The table can contain additional columns.
                """
            ),
        )


@pytest.mark.repeat(5)
async def test_amazon_columns():
    ctx = Context()
    async with WebScraper(
        url="https://www.amazon.co.jp/dp/B0DHCTRH16/",
        scraping_type="single",
    ) as scraper:
        res = await scraper.infer_columns(
            ctx=ctx,
        )

        columns = get_columns(res)

        await llm_assert(
            ctx=ctx,
            output=json.dumps(columns),
            expectations=dedent(
                f"""
                The agent should output a list of dictionaries representing the columns of a table. The table should include the following information:
                
                - The name of the product.
                - The price of the product.
                """,
            ),
            constraints=dedent(
                """
                - The table can contain additional columns.
                """
            ),
        )
