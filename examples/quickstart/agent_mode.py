import asyncio

from npiai.core import create_agent
from npiai.app.google.gmail import Gmail
from examples.utils import load_gmail_credentials


async def main():
    async with create_agent(Gmail(credentials=load_gmail_credentials())) as gmail:
        print(await gmail.chat('get latest email in the inbox'))


if __name__ == "__main__":
    asyncio.run(main())
