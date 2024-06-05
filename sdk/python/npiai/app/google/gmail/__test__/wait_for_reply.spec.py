import asyncio

from npiai.core import create_agent
from npiai.app.google.gmail import Gmail
from google.oauth2.credentials import Credentials


async def main():
    credentials = Credentials.from_authorized_user_file('gmail_token.json')

    async with create_agent(Gmail(credentials)) as gmail:
        return await gmail.chat(
            'Send an email to daofeng@npi.ai inviting him to join an AI meetup and wait for his reply. The date candidates are: Monday, Tuesday, Wednesday'
        )


if __name__ == '__main__':
    asyncio.run(main())
