# pylint: disable=missing-module-docstring
import asyncio
import json

from npi.core.thread import Thread
from npiai_proto import api_pb2
from npi.app.google.calendar import GoogleCalendar


async def main():
    thread = Thread('', api_pb2.GOOGLE_CALENDAR)
    gc = GoogleCalendar()
    await gc.chat(message='get meetings of ww@lifecycle.sh in tomorrow', thread=thread)
    return thread.plaintext()


if __name__ == '__main__':
    res = asyncio.run(main())
    print(json.loads(res))
