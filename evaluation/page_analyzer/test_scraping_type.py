import pytest

from npiai import Context
from npiai.tools.web.page_analyzer import PageAnalyzer

from testdata import testdata


@pytest.mark.parametrize("data", testdata)
async def test_scraping_type(data):
    async with PageAnalyzer() as analyzer:
        res = await analyzer.infer_scraping_type(
            ctx=Context(),
            url=data["url"],
        )

        assert res == data["scraping_type"]
