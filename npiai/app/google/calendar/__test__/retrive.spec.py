# pylint: disable=missing-module-docstring
import asyncio

from npiai import create_agent
from npiai.app.google import GoogleCalendar
from google.oauth2.credentials import Credentials


async def main():
    credentials = Credentials.from_authorized_user_file('gc_token.json')

    async with create_agent(GoogleCalendar(credentials)) as gc:
        return await gc.chat(message='get the incoming 10 events')


if __name__ == '__main__':
    asyncio.run(main())
