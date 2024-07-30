import asyncio
import json
import os
from typing import Literal

import discord

from npiai.context import Context
from npiai.utils import logger
from npiai import FunctionTool, function
from npiai.error.auth import UnauthorizedError

__PROMPT__ = """
You are a Discord Agent helping user send/retrieve messages to/from discord channels. 

For any tool requesting a discord channel ID, you must search for it in the chat history first. 
If not found, you should ask the user to enter the ID through the `ask_human` tool.

## Example

Task: Send a DM to {{some_user}} and wait for their reply.
Workflow:
- ask_for_id({ "name": "user" })
- create_dm({ "user_id": "{{user_id}}" })
- send_message({ "channel_id": "{{dm_channel_id}}", "content": "Hi there!" })
- wait_for_reply({ "channel_id": "{{dm_channel_id}}", "message_id": "{{message_id}}" })

Task: Get the latest message from {{some_channel}}.
Workflow:
- ask_for_id({ "name": "channel" })
- fetch_history({ "channel_id": "{{channel_id}}" })

Task: Send a message to {{some_channel}}.
Workflow:
- ask_for_id({ "name": "channel" })
- send_message({ "channel_id": "{{channel_id}}", "content": "Hi there!" })
"""


class Discord(FunctionTool):
    name = "discord"
    description = "Send/Retrieve messages to/from discord channels"
    system_prompt = __PROMPT__

    _client: discord.Client
    _access_token: str

    def __init__(self, access_token: str = None):
        super().__init__()

        self._access_token = access_token or os.environ.get(
            "DISCORD_ACCESS_TOKEN", None
        )

        self._client = discord.Client(intents=discord.Intents.default())

    async def start(self):
        if self._access_token is None:
            raise UnauthorizedError("Discord credentials are not found")

        await super().start()
        await self._client.login(self._access_token)

    async def end(self):
        await super().end()
        await self._client.close()

    def parse_user(self, user: discord.User):
        return {
            "id": user.id,
            "name": user.name,
        }

    def parse_message(self, msg: discord.Message):
        return {
            "id": msg.id,
            "author": self.parse_user(msg.author),
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
            "reply_to_message_id": msg.reference.message_id if msg.reference else None,
            "mentions": [self.parse_user(user) for user in msg.mentions],
            "mention_everyone": msg.mention_everyone,
        }

    @function
    async def ask_for_id(
        self, ctx: Context, name: Literal["user", "channel", "message"]
    ):
        """
        Ask the user to provide recipient's user id, channel id, or message id.
        Args:
            ctx: NPi context.
            name: The type of id to ask for.
        """
        return await self.hitl.input(
            ctx,
            self.name,
            f"Please provide recipient's {name} ID to send messages to",
        )

    @function
    async def create_dm(self, user_id: int):
        """
        Create a direct message channel with a specific user.

        Args:
            user_id: The ID of the **user** who will receive the direct message. Note that this is not the channel ID.
        """
        user = await self._client.fetch_user(user_id)
        channel = await user.create_dm()

        return f"Direct message channel created. Channel ID: {channel.id}"

    @function
    async def fetch_history(self, channel_id: int, max_results: int = 1):
        """
        Fetch history messages from the discord channel with the given channel ID.

        Args:
            channel_id: The ID of the **channel** to send the message to. You should ask the user for it if not provided.
            max_results: The maximum number of messages to fetch.
        """
        channel = await self._client.fetch_channel(channel_id)
        messages = []

        async for msg in channel.history(limit=max_results):
            messages.append(self.parse_message(msg))

        logger.debug(
            f"[{self.name}]: Fetched {len(messages)} messages: {json.dumps(messages, indent=2, ensure_ascii=False)}"
        )

        return json.dumps(messages, ensure_ascii=False)

    @function
    async def send_message(self, channel_id: int, content: str):
        """
        Send a message to the discord channel with the given channel ID.

        Args:
            channel_id: The ID of the **channel** to send the message to. You should ask the user for it if not provided.
            content: The message to send.
        """
        channel = await self._client.fetch_channel(channel_id)
        msg = await channel.send(content)

        logger.debug(f"[{self.name}]: Sent message: (id: {msg.id}) {msg.content}")

        return f"Message sent. ID: {msg.id}"

    @function
    async def reply(self, channel_id: int, message_id: int, content: str):
        """
        Reply to a message in the discord channel with the given channel ID.

        Args:
            channel_id: The ID of the **channel** to send the message to. You should ask the user for it if not provided.
            message_id: The ID of the message to reply. You should ask the user for it if not provided.
            content: The message to reply.
        """
        channel = await self._client.fetch_channel(channel_id)
        msg = await channel.fetch_message(message_id)
        reply = await msg.reply(content)

        logger.debug(
            f"[{self.name}]: Created reply for message ID {msg.id}. Reply: (id: {reply.id}) {reply.content}"
        )

        return f"Created reply for message ID {msg.id}. Reply ID: {reply.id}"

    @function
    async def wait_for_reply(self, channel_id: int, message_id: int):
        """
        Wait for a reply to the given message in the discord channel with the given channel ID.

        Args:
            channel_id: The ID of the **channel** to send the message to. You should ask the user for it if not provided.
            message_id: The ID of the message being replied to. You should ask the user for it if not provided.
        """
        channel = await self._client.fetch_channel(channel_id)
        ref_msg = await channel.fetch_message(message_id)
        last_msg = ref_msg

        while True:
            history = channel.history(limit=10, after=last_msg.created_at)

            async for msg in history:
                # if (msg.reference and msg.reference.message_id == ref_msg.id) or \
                #     msg.mention_everyone or \
                #     any(user.id == ref_msg.author.id for user in msg.mentions):
                if msg.author.id != ref_msg.author.id and (
                    not msg.reference or msg.reference.message_id == ref_msg.id
                ):
                    return f"Received reply. {json.dumps(self.parse_message(msg))}"

                last_msg = msg

            await asyncio.sleep(3)
