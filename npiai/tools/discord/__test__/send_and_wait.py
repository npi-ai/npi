import asyncio

from npiai import agent
from npiai.tools import Discord
from npiai.hitl_handler import ConsoleHandler


async def main():
    async with agent.wrap(Discord()) as agent:
        agent.use_hitl(ConsoleHandler())
        return await agent.chat(
            'Send a direct message to Dolphin asking if he is doing well, and wait for his reply.'
        )


if __name__ == '__main__':
    asyncio.run(main())
