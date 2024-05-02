from pydantic import Field
from npi.types import Parameters


class BaseChannelParameters(Parameters):
    channel_id: str = Field(
        description='The ID of the **channel** to send the message to. You should ask the user for it if not provided.'
    )


class CreateDMParameters(Parameters):
    user_id: str = Field(
        description='The ID of the **user** who will receive the direct message. Note that this is not the channel ID.'
    )


class SendMessageParameters(BaseChannelParameters):
    content: str = Field(description='The message to send.')


class FetchHistoryParameters(BaseChannelParameters):
    max_results: int = Field(default=1, description='The maximum number of messages to fetch.')


class ReplyParameters(BaseChannelParameters):
    thread_id: str = Field(
        description='The ID of the thread to reply. You should ask the user for it if not provided.'
    )
    content: str = Field(description='The message to reply.')


class WaitForReplyParameters(BaseChannelParameters):
    thread_id: str = Field(
        description='The ID of the thread being replied to. You should ask the user for it if not provided.'
    )
