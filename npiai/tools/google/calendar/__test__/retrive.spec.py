# pylint: disable=missing-module-docstring
import asyncio

from npiai import agent
from npiai.tools.google import GoogleCalendar
from google.oauth2.credentials import Credentials


async def main():
    credentials = Credentials.from_authorized_user_file("gc_token.json")

    async with agent.wrap(GoogleCalendar(credentials)) as gc:
        return await gc.chat(instruction="get the incoming 10 events")


if __name__ == "__main__":
    asyncio.run(main())
