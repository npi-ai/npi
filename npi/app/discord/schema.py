from pydantic import Field
from npi.types import Parameters


class BaseChannelParameters(Parameters):
    channel_id: int = Field(
        description='The ID of the **channel** to send the message to. You should ask the user for it if not provided.'
    )


class CreateDMParameters(Parameters):
    user_id: int = Field(
        description='The ID of the **user** who will receive the direct message. Note that this is not the channel ID.'
    )


class FetchHistoryParameters(BaseChannelParameters):
    max_results: int = Field(default=1, description='The maximum number of messages to fetch.')


class SendMessageParameters(BaseChannelParameters):
    content: str = Field(description='The message to send.')


class ReplyParameters(BaseChannelParameters):
    message_id: int = Field(
        description='The ID of the message to reply. You should ask the user for it if not provided.'
    )
    content: str = Field(description='The message to reply.')


class WaitForReplyParameters(BaseChannelParameters):
    message_id: int = Field(
        description='The ID of the message being replied to. You should ask the user for it if not provided.'
    )
