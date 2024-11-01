import pytest

from npiai import Context
from npiai.tools.web.page_analyzer import PageAnalyzer

from testdata import testdata

testdata_with_selectors = [item for item in testdata if "selectors" in item]


@pytest.mark.parametrize("data", testdata_with_selectors)
async def test_selectors(data):
    if "selectors" not in data:
        return

    async with PageAnalyzer() as analyzer:
        res = await analyzer.infer_similar_items_selector(
            ctx=Context(),
            url=data["url"],
        )

        assert (
            res is not None
        ), f"Expected selectors for {data['url']}: {data['selectors']}"

        assert res["ancestor"] == data["selectors"]["ancestor"]
        assert res["items"] == data["selectors"]["items"]
