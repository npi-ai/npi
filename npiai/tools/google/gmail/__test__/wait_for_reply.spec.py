import asyncio

from npiai import agent
from npiai.tools.google import Gmail
from google.oauth2.credentials import Credentials


async def main():
    credentials = Credentials.from_authorized_user_file("gmail_token.json")

    async with agent.wrap(Gmail(credentials)) as gmail:
        return await gmail.chat(
            "Send an email to daofeng@npi.ai inviting him to join an AI meetup and wait for his reply. The date candidates are: Monday, Tuesday, Wednesday"
        )


if __name__ == "__main__":
    asyncio.run(main())
