import asyncio

from npiai import agent_wrapper
from npiai.app.slack import Slack


async def main():
    async with agent_wrapper(Slack()) as slack:
        return await slack.chat(
            'Send a direct message to Dolphin (user id: "U071QBWBVCJ") asking if he is doing well, and wait for his reply.'
        )


if __name__ == '__main__':
    asyncio.run(main())
