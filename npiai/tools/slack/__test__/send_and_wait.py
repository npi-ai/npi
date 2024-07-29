import asyncio

from npiai import agent
from npiai.tools import Slack
from npiai.hitl_handler import ConsoleHandler


async def main():
    async with agent.wrap(Slack()) as slack:
        slack.use_hitl(ConsoleHandler())

        return await slack.chat(
            "Send a direct message to Dolphin asking if he is doing well, and wait for his reply."
        )


if __name__ == "__main__":
    asyncio.run(main())
