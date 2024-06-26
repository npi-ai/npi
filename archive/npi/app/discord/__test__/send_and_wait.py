import asyncio

from npi.app.discord import Discord
from utils import test_init_discord_cred


async def main():
    discord = Discord()
    res = await discord.chat(
        'Send a direct message to Dolphin (user id: 209243186332303362) asking if he is doing well, and wait for his reply.'
    )
    await discord.dispose()
    return res


if __name__ == '__main__':
    test_init_discord_cred()
    asyncio.run(main())
