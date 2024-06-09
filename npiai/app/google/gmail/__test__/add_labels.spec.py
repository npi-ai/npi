import asyncio

from npiai import agent_wrapper
from npiai.app.google import Gmail
from google.oauth2.credentials import Credentials


async def main():
    credentials = Credentials.from_authorized_user_file('gmail_token.json')

    async with agent_wrapper(Gmail(credentials)) as gmail:
        return await gmail.chat('Add label "TEST" to the latest email from daofeng.wu@emory.edu')


if __name__ == '__main__':
    asyncio.run(main())
