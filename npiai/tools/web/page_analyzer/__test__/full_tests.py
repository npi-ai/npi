import asyncio
from npiai.tools.web.page_analyzer import PageAnalyzer

# from npiai.utils.test_utils import DebugContext
from npiai import Context

urls = [
    "https://www.bardeen.ai/playbooks",
    "https://ifttt.com/explore",
    "https://retool.com/templates",
    "https://www.google.com/search?q=test",
    "https://www.amazon.com/s?k=test",
]


async def main():
    async with PageAnalyzer(headless=False) as analyzer:
        for url in urls:
            print(f"Analyzing {url}:")

            infinite_scroll = await analyzer.support_infinite_scroll(
                url=url,
            )

            print("  - Support infinite scroll:", infinite_scroll)

            pagination = await analyzer.get_pagination_button(
                ctx=Context(),
                url=url,
            )

            print("  - Pagination button:", pagination)

            print()


if __name__ == "__main__":
    asyncio.run(main())
