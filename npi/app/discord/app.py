import asyncio
import json

import discord

from npi.utils import logger
from npi.core import App, npi_tool
from npi.config import config
from npi.error.auth import UnauthorizedError
from npi.core.thread import Thread
from .schema import *

__PROMPT__ = """
You are a Discord Agent helping user send/retrieve messages to/from discord channels. 

For any tool requesting a discord channel ID, you must search for it in the chat history first. 
If not found, you should ask the user to enter the ID through the `ask_human` tool.

## Example

Task: Send a DM to {{some_user}} and wait for their reply.
Workflow:
- Ask the user for {{some_user}}'s ID. Record it as {{user_id}}.
- Create a DM channel with user {{user_id}}. Record the DM channel ID {{channel_id}}.
- Send a message in the DM channel. Record the message ID {{message_id}}.
- Wait for the reply for message {{message_id}} to appear in channel {{channel_id}}.

Task: Get the latest message from {{some_channel}}.
Workflow:
- Ask the user for the {{some_channel}}'s ID. Record it as {{channel_id}}.
- Fetch the latest message from {{channel_id}}.

Task: Send a message to {{some_channel}}.
Workflow:
- Ask the user for the {{some_channel}}'s ID. Record it as {{channel_id}}.
- Send a message to {{channel_id}}.
"""


class Discord(App):
    client: discord.Client
    _access_token: str

    def __init__(self, llm=None):
        cred = config.get_discord_credentials()

        if cred is None:
            raise UnauthorizedError("Discord credentials are not found, please use `npi auth discord` first")

        super().__init__(
            name='discord',
            description='Send/Retrieve messages to/from discord channels',
            system_role=__PROMPT__,
            llm=llm,
        )

        self.client = discord.Client(intents=discord.Intents.default())
        self._access_token = cred.access_token

    async def start(self, thread: Thread = None):
        await super().start(thread)
        await self.client.login(self._access_token)

    async def dispose(self):
        await super().dispose()
        await self.client.close()

    def parse_user(self, user: discord.User):
        return {
            'id': user.id,
            'name': user.name,
        }

    def parse_message(self, msg: discord.Message):
        return {
            'id': msg.id,
            'author': self.parse_user(msg.author),
            'content': msg.content,
            'created_at': msg.created_at.isoformat(),
            'reply_to_message_id': msg.reference.message_id if msg.reference else None,
            'mentions': [self.parse_user(user) for user in msg.mentions],
            'mention_everyone': msg.mention_everyone,
        }

    @npi_tool
    async def create_dm(self, params: CreateDMParameters):
        """Create a direct message channel with a specific user"""
        user = await self.client.fetch_user(params.user_id)
        channel = await user.create_dm()

        return f'Direct message channel created. Channel ID: {channel.id}'

    @npi_tool
    async def fetch_history(self, params: FetchHistoryParameters):
        """Fetch history messages from the discord channel with the given channel ID"""
        channel = await self.client.fetch_channel(params.channel_id)
        messages = []

        async for msg in channel.history(limit=params.max_results):
            messages.append(self.parse_message(msg))

        logger.debug(
            f'[{self.name}]: Fetched {len(messages)} messages: {json.dumps(messages, indent=2, ensure_ascii=False)}'
        )

        return json.dumps(messages, ensure_ascii=False)

    @npi_tool
    async def send_message(self, params: SendMessageParameters):
        """Send a message to the discord channel with the given channel ID"""
        channel = await self.client.fetch_channel(params.channel_id)
        msg = await channel.send(params.content)

        logger.debug(f'[{self.name}]: Sent message: (id: {msg.id}) {msg.content}')

        return f'Message sent. ID: {msg.id}'

    @npi_tool
    async def reply(self, params: ReplyParameters):
        """Reply to a message in the discord channel with the given channel ID"""
        channel = await self.client.fetch_channel(params.channel_id)
        msg = await channel.fetch_message(params.message_id)
        reply = await msg.reply(params.content)

        logger.debug(f'[{self.name}]: Created reply for message ID {msg.id}. Reply: (id: {reply.id}) {reply.content}')

        return f'Created reply for message ID {msg.id}. Reply ID: {reply.id}'

    @npi_tool
    async def wait_for_reply(self, params: WaitForReplyParameters):
        """Wait for a reply to the given message in the discord channel with the given channel ID"""
        channel = await self.client.fetch_channel(params.channel_id)
        ref_msg = await channel.fetch_message(params.message_id)
        last_msg = ref_msg

        while True:
            history = channel.history(limit=10, after=last_msg.created_at)

            async for msg in history:
                # if (msg.reference and msg.reference.message_id == ref_msg.id) or \
                #     msg.mention_everyone or \
                #     any(user.id == ref_msg.author.id for user in msg.mentions):
                if msg.author.id != ref_msg.author.id and \
                        (not msg.reference or msg.reference.message_id == ref_msg.id):
                    return f'Received reply. {json.dumps(self.parse_message(msg))}'

                last_msg = msg

            await asyncio.sleep(3)
