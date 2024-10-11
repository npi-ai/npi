import asyncio
from npiai.tools.web.page_analyzer import PageAnalyzer
from npiai.utils.test_utils import DebugContext


async def main():
    async with PageAnalyzer(headless=False) as analyzer:
        pagination = await analyzer.get_pagination_button(
            ctx=DebugContext(),
            url="https://www.google.com/search?q=test",
        )

        print("Pagination button:", pagination)


if __name__ == "__main__":
    asyncio.run(main())
