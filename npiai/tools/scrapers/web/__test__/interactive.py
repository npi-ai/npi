import asyncio

from npiai.utils.test_utils import DebugContext

# from npiai import Context
from utils import auto_scrape
from npiai.hitl_handler import ConsoleHandler


async def main():
    url = input("Enter the URL: ")
    ctx = DebugContext()
    ctx.use_hitl(ConsoleHandler())
    # url = "https://www.bardeen.ai/playbooks"

    await auto_scrape(
        ctx=ctx,
        url=url,
    )


if __name__ == "__main__":
    asyncio.run(main())
