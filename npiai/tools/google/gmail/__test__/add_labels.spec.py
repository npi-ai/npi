import asyncio

from npiai import agent
from npiai.tools.google import Gmail
from google.oauth2.credentials import Credentials


async def main():
    credentials = Credentials.from_authorized_user_file("gmail_token.json")

    async with agent.wrap(Gmail(credentials)) as gmail:
        return await gmail.chat(
            'Add label "TEST" to the latest email from daofeng.wu@emory.edu'
        )


if __name__ == "__main__":
    asyncio.run(main())
