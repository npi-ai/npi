import asyncio
from npiai import agent_wrapper
from npiai.browser_app.browser import Browser


async def main():
    async with agent_wrapper(Browser(headless=False)) as browser:
        return await browser.chat(
            'Book a one-way flight from ATL to LAX on 4/20 using Google Flights.'
        )


if __name__ == '__main__':
    asyncio.run(main())
