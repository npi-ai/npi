import pytest

from npiai.tools.web.page_analyzer import PageAnalyzer

from testdata import testdata


@pytest.mark.parametrize("data", testdata)
async def test_infinite_scroll(data):
    async with PageAnalyzer() as analyzer:
        items_selector = data["selectors"]["items"] if "selectors" in data else None

        res = await analyzer.support_infinite_scroll(
            url=data["url"],
            items_selector=items_selector,
        )

        assert res == data["infinite_scroll"]
