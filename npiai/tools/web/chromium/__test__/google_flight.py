import asyncio
from npiai import agent_wrapper
from npiai.tools.web.chromium import Chromium


async def main():
    async with agent_wrapper(Chromium(headless=False)) as browser:
        return await browser.chat(
            'Book a one-way flight from ATL to LAX on 4/20 using Google Flights.'
        )


if __name__ == '__main__':
    asyncio.run(main())
