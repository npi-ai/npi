import asyncio
from npi.browser_app.general_browser_agent import GeneralBrowserAgent


async def main():
    agent = GeneralBrowserAgent(headless=False)
    return await agent.chat(
        'Book a one-way flight from ATL to LAX on 4/20 using Google Flights.'
    )


if __name__ == '__main__':
    res = asyncio.run(main())
    print(res)
