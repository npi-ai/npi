import pytest

from npiai import Context
from npiai.tools.web.page_analyzer import PageAnalyzer

from testdata import testdata


@pytest.mark.parametrize("data", testdata)
async def test_pagination(data):
    async with PageAnalyzer() as analyzer:
        res = await analyzer.get_pagination_button(
            ctx=Context(),
            url=data["url"],
        )

        assert res == data["pagination_button"]
