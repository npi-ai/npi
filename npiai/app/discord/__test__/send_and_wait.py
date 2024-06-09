import asyncio

from npiai import agent_wrapper
from npiai.app.discord import Discord


async def main():
    async with agent_wrapper(Discord()) as discord:
        return await discord.chat(
            'Send a direct message to Dolphin (user id: 209243186332303362) asking if he is doing well, and wait for his reply.'
        )


if __name__ == '__main__':
    asyncio.run(main())
