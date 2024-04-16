import asyncio

from npi.app.google.gmail import Gmail
from npi.core.thread import Thread
from proto.python.api import api_pb2


async def main():
    thread = Thread('', api_pb2.GOOGLE_GMAIL)
    gmail = Gmail()
    await gmail.chat(
        'Send an email to daofeng.wu@emory.edu inviting him to join an AI meetup and wait for his reply. The date candidates are: Monday, Tuesday, Wednesday',
        thread,
    )
    await gmail.chat('Wait for reply from the last message', thread)
    return thread.plaintext()


if __name__ == '__main__':
    res = asyncio.run(main())
    print(res)
