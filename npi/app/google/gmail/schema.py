from pydantic import Field
from textwrap import dedent
from typing import Optional, List
from npi.types import Parameter


class SearchEmailsParameter(Parameter):
    query: Optional[str] = Field(default=None, description='A Gmail query to match emails')
    max_results: int = Field(default=100, description='Maximum number of messages to return')


class SendEmailParameter(Parameter):
    to: str = Field(description='The email address the message is being sent to')
    subject: str = Field(description='The subject line of the email')
    message: Optional[str] = Field(default=None, description='The email content in markdown format')
    cc: Optional[List[str]] = Field(default=None, description='The list of email addresses to be cc\'d')
    bcc: Optional[List[str]] = Field(default=None, description='The list of email addresses to be bcc\'d')


class ReplyParameter(SendEmailParameter):
    message: str = Field(
        description=dedent(
            """
            The reply message in markdown format. You should also quote the email being replied to.
            For example, given the following message:
                Message ID: 18eaefa2c6b35409
                Thread ID: 18eaf09f637a31a9
                Sender ID: <qbvDktEYR9KqlLxxrp6s-w@geopod-ismtpd-15>
                From: "Test" <test@gmail.com>
                To: "Me" <me@gmail.com>
                Date: 2024-04-05 23:30:27+09:00
                Subject: Greeting
                Content: Hello there!
            You should generate a reply message like:
                Hey! How can I help you?
                
                On Apr 5, 2024 at 23:30:27, Test <test@gmail.com> wrote:
                > Hello there!
            """
        )
    )
    recipient_id: str = Field(
        description='The ID of the recipient being replied to. You can find this in the "Sender ID: ..." line of the email'
    )


class CreateDraftParameter(SendEmailParameter):
    pass


class CreateReplyDraftParameter(ReplyParameter):
    pass


class AddLabelsParameter(Parameter):
    message_ids: List[str] = Field(
        description='A list of IDs of messages that should be labeled. You can find this in the "Message ID: ..." line of the email'
    )
    labels: List[str] = Field(description='A list of labels to add')


class RemoveLabelsParameter(Parameter):
    message_ids: List[str] = Field(
        description='A list of IDs of messages that should be labeled. You can find this in the "Message ID: ..." line of the email'
    )
    labels: List[str] = Field(description='A list of labels to remove')


class WaitForReplyParameter(Parameter):
    # TODO: how to check correct thread?
    # thread_id: str = Field(
    #     description='The ID of the thread to wait. You can find this in the "Thread ID: ..." line of the email'
    # )
    sent_from: str = Field(
        description='The reply message sender. This should be the recipient of the last email and you can find it in the "To: ..." line'
    )
