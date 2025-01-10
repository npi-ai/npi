import asyncio

from npiai.utils.test_utils import DebugContext

# from npiai import Context
from utils import auto_scrape


async def main():
    url = input("Enter the URL: ")
    # url = "https://www.bardeen.ai/playbooks"

    await auto_scrape(
        ctx=DebugContext(),
        url=url,
    )


if __name__ == "__main__":
    asyncio.run(main())
