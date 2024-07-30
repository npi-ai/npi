import asyncio
import json
import os
from typing import Literal

from slack_sdk.web.async_client import AsyncWebClient, AsyncSlackResponse

from npiai.context import Context
from npiai.utils import logger
from npiai import FunctionTool, function
from npiai.error.auth import UnauthorizedError

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


class Slack(FunctionTool):
    name = "slack"
    description = "Send/Retrieve messages to/from Slack channels"
    system_prompt = __PROMPT__

    _access_token: str | None
    _client: AsyncWebClient
    _user_id: str = None

    def __init__(self, access_token: str = None):
        super().__init__()
        self._access_token = access_token or os.environ.get("SLACK_ACCESS_TOKEN", None)

    async def start(self):
        if self._access_token is None:
            raise UnauthorizedError("Slack credentials are not found")

        self._client = AsyncWebClient(token=self._access_token)

    async def _get_user_id(self) -> str:
        if not self._user_id:
            res = await self._client.auth_test()
            self._user_id = res["user_id"]

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

        for msg in response["messages"]:
            if msg["type"] != "message":
                continue
            messages.append(self._parse_raw_message(msg))

        return sorted(messages, key=lambda x: float(x["thread_id"]))

    @function
    async def ask_for_id(
        self, ctx: Context, name: Literal["user", "channel", "thread"]
    ):
        """
        Ask the user to provide recipient's user id, channel id, or thread id.
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
    async def list_channels(self):
        """Get a list of all Slack channels"""
        res = await self._client.conversations_list()
        channels = []

        for chn in res["channels"]:
            channels.append(
                {
                    "id": chn["id"],
                    "name": chn["name"],
                }
            )

        return json.dumps(channels, ensure_ascii=False)

    @function
    async def create_dm(self, user_id: str):
        """
        Create a direct message channel with a specific user.

        Args:
            user_id: The ID of the **user** who will receive the direct message. Note that this is not the channel ID.
        """
        res = await self._client.conversations_open(users=[user_id])

        return f'Direct message channel created. Channel ID: {res["channel"]["id"]}'

    @function
    async def send_message(self, channel_id: str, message: str):
        """
        Send a message to the Slack channel with the given channel ID.

        Args:
            channel_id: The ID of the **channel** to send the message to. You should ask the user for it if not provided.
            message: The message to send.
        """
        res = await self._client.chat_postMessage(
            channel=channel_id,
            text=message,
        )

        msg = res["message"]

        logger.debug(f'[{self.name}]: Sent message: (id: {msg["ts"]}) {msg["text"]}')

        return f'Message sent. Thread ID: {msg["ts"]}'

    @function
    async def fetch_history(self, channel_id: str, max_messages: int = 1):
        """
        Fetch history messages from the Slack channel with the given channel ID.

        Args:
            channel_id: The ID of the **channel** to fetch the history from.
            max_messages: The maximum number of messages to fetch.
        """
        res = await self._client.conversations_history(
            channel=channel_id, limit=max_messages
        )
        messages = self._get_messages_from_response(res)

        logger.debug(
            f"[{self.name}]: Fetched {len(messages)} messages: {json.dumps(messages, indent=2, ensure_ascii=False)}"
        )

        return json.dumps(messages, ensure_ascii=False)

    @function
    async def reply(self, channel_id: str, thread_id: str, message: str):
        """
        Reply to a context in the Slack channel with the given channel ID.

        Args:
            channel_id: The ID of the **channel** to reply to.
            thread_id: The ID of the **context** to reply to.
            message: The message to reply.
        """
        res = await self._client.chat_postMessage(
            channel=channel_id,
            text=message,
            thread_ts=thread_id,
        )

        msg = res["message"]

        logger.debug(
            f'[{self.name}]: Created reply for context ID {thread_id}. Reply: (id: {msg["ts"]}) {msg["text"]}'
        )

        return f'Created reply for message ID {msg.id}. Reply ID: {msg["ts"]}'

    @function
    async def wait_for_reply(self, channel_id: str, thread_id: str):
        """
        Wait for a reply to the given context in the Slack channel with the given channel ID.

        Args:
            channel_id: The ID of the **channel** to wait for.
            thread_id: The ID of the **context** to wait for.
        """
        last_ts = thread_id

        while True:
            # check threaded replies
            thread_res = await self._client.conversations_replies(
                channel=channel_id,
                ts=thread_id,
            )

            if len(thread_res["messages"]) > 1:
                messages = self._get_messages_from_response(thread_res)[1:]

                logger.debug(
                    f"[{self.name}]: Found {len(messages)} context replies: {json.dumps(messages, indent=2, ensure_ascii=False)}"
                )

                return json.dumps(messages, ensure_ascii=False)

            # check channel replies
            channel_res = await self._client.conversations_history(
                channel=channel_id,
                oldest=last_ts,
                inclusive=False,
                limit=10,
            )

            for msg in channel_res["messages"]:
                if (
                    msg["type"] == "message"
                    and msg["user"] != await self._get_user_id()
                ):
                    messages = [self._parse_raw_message(msg)]

                    logger.debug(
                        f"[{self.name}]: Received a new message: {json.dumps(messages, indent=2, ensure_ascii=False)}"
                    )

                    return json.dumps(messages, ensure_ascii=False)

            await asyncio.sleep(3)
