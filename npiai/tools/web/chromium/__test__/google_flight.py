import asyncio
from npiai import agent
from npiai.tools.web.chromium import Chromium
from npiai.utils.test_utils import DebugContext


async def main():
    async with agent.wrap(Chromium(headless=False)) as browser:
        return await browser.chat(
            ctx=DebugContext(),
            instruction="Book a one-way flight from ATL to LAX on 4/20 using Google Flights.",
        )


if __name__ == "__main__":
    asyncio.run(main())
