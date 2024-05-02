import asyncio
import json
import os

from slack_sdk import WebClient
from slack_sdk.web.async_client import AsyncWebClient, AsyncSlackResponse

from npi.utils import logger
from npi.core import App, npi_tool
from npi.config import config
from npi.error.auth import UnauthorizedError

from .schema import *

__PROMPT__ = """
You are a Slack Agent helping user send/retrieve messages to/from discord channels. 

For any tool requesting a discord channel ID, you must search for it in the chat history first. 
If not found, you should ask the user to enter the ID.

## Example

Task: Send a DM to user {{user_id}} and wait for their reply.
Workflow:
- Create a DM channel with user {{user_id}}. Record the DM channel ID {{channel_id}}.
- Send a message in the DM channel. Record the message ID {{message_id}}.
- Wait for the reply for message {{message_id}} to appear in channel {{channel_id}}.
"""


class Slack(App):
    client: AsyncWebClient
    _user_id: str = None

    def __init__(self, llm=None):
        cred = config.get_slack_credentials()

        if cred is None:
            raise UnauthorizedError("Slack credentials are not found, please use `npi auth slack` first")

        super().__init__(
            name='slack',
            description='Send/Retrieve messages to/from Slack channels',
            system_role=__PROMPT__,
            llm=llm,
        )

        self.client = AsyncWebClient(token=cred.access_token)

    async def _get_user_id(self) -> str:
        if not self._user_id:
            res = await self.client.auth_test()
            self._user_id = res['user_id']

        return self._user_id

    @staticmethod
    def _parse_raw_message(raw_message: dict):
        return {
            "thread_id": raw_message["ts"],
            "user": raw_message["user"],
            "content": raw_message["text"],
            "reply_count": raw_message.get("reply_count", 0),
        }

    def _get_messages_from_response(self, response: AsyncSlackResponse):
        messages = []

        for msg in response['messages']:
            if msg['type'] != 'message':
                continue
            messages.append(self._parse_raw_message(msg))

        return sorted(messages, key=lambda x: float(x['thread_id']))

    @npi_tool
    async def list_channels(self):
        """Get a list of all Slack channels"""
        res = await self.client.conversations_list()
        channels = []

        for chn in res["channels"]:
            channels.append(
                {
                    "id": chn["id"],
                    "name": chn["name"],
                }
            )

        return json.dumps(channels, ensure_ascii=False)

    @npi_tool
    async def create_dm(self, params: CreateDMParameters):
        """Create a direct message channel with a specific user"""
        res = await self.client.conversations_open(users=[params.user_id])

        return f'Direct message channel created. Channel ID: {res["channel"]["id"]}'

    @npi_tool
    async def send_message(self, params: SendMessageParameters):
        """Send a message to the Slack channel with the given channel ID"""
        res = await self.client.chat_postMessage(
            channel=params.channel_id,
            text=params.content,
        )

        msg = res['message']

        logger.debug(f'[{self.name}]: Sent message: (id: {msg["ts"]}) {msg["text"]}')

        return f'Message sent. Thread ID: {msg["ts"]}'

    @npi_tool
    async def fetch_history(self, params: FetchHistoryParameters):
        """Fetch history messages from the Slack channel with the given channel ID"""
        res = await self.client.conversations_history(channel=params.channel_id, limit=params.max_results)
        messages = self._get_messages_from_response(res)

        logger.debug(
            f'[{self.name}]: Fetched {len(messages)} messages: {json.dumps(messages, indent=2, ensure_ascii=False)}'
        )

        return json.dumps(messages, ensure_ascii=False)

    @npi_tool
    async def reply(self, params: ReplyParameters):
        """Reply to a thread in the Slack channel with the given channel ID"""
        res = await self.client.chat_postMessage(
            channel=params.channel_id,
            text=params.content,
            thread_ts=params.thread_id,
        )

        msg = res['message']

        logger.debug(
            f'[{self.name}]: Created reply for thread ID {params.thread_id}. Reply: (id: {msg["ts"]}) {msg["text"]}'
        )

        return f'Created reply for message ID {msg.id}. Reply ID: {msg["ts"]}'

    @npi_tool
    async def wait_for_reply(self, params: WaitForReplyParameters):
        """Wait for a reply to the given thread in the Slack channel with the given channel ID"""
        last_ts = params.thread_id

        while True:
            # check threaded replies
            thread_res = await self.client.conversations_replies(
                channel=params.channel_id,
                ts=params.thread_id,
            )

            if len(thread_res['messages']) > 1:
                messages = self._get_messages_from_response(thread_res)[1:]

                logger.debug(
                    f'[{self.name}]: Found {len(messages)} thread replies: {json.dumps(messages, indent=2, ensure_ascii=False)}'
                )

                return json.dumps(messages, ensure_ascii=False)

            # check channel replies
            channel_res = await self.client.conversations_history(
                channel=params.channel_id,
                oldest=last_ts,
                inclusive=False,
                limit=10,
            )

            for msg in channel_res['messages']:
                if msg['type'] == 'message' and msg['user'] != await self._get_user_id():
                    messages = [self._parse_raw_message(msg)]

                    logger.debug(
                        f'[{self.name}]: Received a new message: {json.dumps(messages, indent=2, ensure_ascii=False)}'
                    )

                    return json.dumps(messages, ensure_ascii=False)

            await asyncio.sleep(3)
