import json
from textwrap import dedent
from typing import AsyncGenerator, List, Dict
import pytest

from npiai.tools.web.scraper import Scraper
from npiai.context import Context
from npiai.evaluation import llm_assert

list_like_output_columns = [
    {
        "name": "Apps Involved",
        "description": "The apps involved in the playbook",
    },
    {
        "name": "Description",
        "description": "The description of the playbook",
    },
    {
        "name": "Time Saved",
        "description": "The time saved by using the playbook",
    },
    {
        "name": "URL",
        "description": "The URL of the playbook",
    },
]


async def collect_results(stream: AsyncGenerator[List[Dict[str, str]], None]):
    results = []
    async for items in stream:
        results.extend(items)
    return results


@pytest.fixture(scope="module", autouse=True)
async def list_like_scraping_results():
    async with Scraper() as scraper:
        stream = scraper.summarize_stream(
            ctx=Context(),
            url="https://www.bardeen.ai/playbooks",
            scraping_type="list-like",
            ancestor_selector=".playbook_list",
            items_selector=".playbook_list .playbook_item-link",
            output_columns=list_like_output_columns,
            limit=10,
        )

        return await collect_results(stream)


def test_list_like_results_length(list_like_scraping_results):
    assert (
        len(list_like_scraping_results) <= 10
    ), "The agent should output at most 10 results."


async def test_list_like_columns(list_like_scraping_results):
    await llm_assert(
        json.dumps(list_like_scraping_results),
        dedent(
            f"""
            The agent should output a list of dictionaries, where each dictionary has the following keys:
            {json.dumps(list_like_output_columns)}
            """
        ),
    )
