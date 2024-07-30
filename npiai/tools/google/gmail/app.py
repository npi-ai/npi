import asyncio
import json
import os
from typing import List
from textwrap import dedent

from googleapiclient.errors import HttpError
from markdown import markdown
from simplegmail.message import Message

from npiai import FunctionTool, function
from npiai.error import UnauthorizedError
from npiai.context import Context

from google.oauth2.credentials import Credentials as GoogleCredentials
from oauth2client.client import OAuth2Credentials

from .client import GmailClientWrapper


def convert_google_cred_to_oauth2_cred(
    google_credentials: GoogleCredentials,
) -> OAuth2Credentials:
    # Convert expiry datetime to string if necessary
    expiry = (
        google_credentials.expiry.isoformat() if google_credentials.expiry else None
    )

    # Create an instance of OAuth2Credentials
    return OAuth2Credentials(
        access_token=google_credentials.token,
        client_id=google_credentials.client_id,
        client_secret=google_credentials.client_secret,
        refresh_token=google_credentials.refresh_token,
        token_expiry=google_credentials.expiry,
        token_uri=google_credentials.token_uri,
        user_agent=None,  # or any user agent you have
        scopes=google_credentials.scopes,
    )


class Gmail(FunctionTool):
    name = "gmail"
    description = 'interact with Gmail using English, e.g., gmail("send an email to test@gmail.com")'
    system_prompt = "You are a Gmail Agent helping users to manage their emails"

    _creds: GoogleCredentials | None
    _gmail_client: GmailClientWrapper

    def __init__(self, creds: GoogleCredentials | None = None):
        super().__init__()
        self._creds = creds

    async def start(self):
        if self._creds is None:
            cred_file = os.environ.get("GOOGLE_CREDENTIAL")
            if cred_file is None:
                raise UnauthorizedError("Google credential file not found")
            self._creds = GoogleCredentials.from_authorized_user_file(
                filename=cred_file, scopes="https://mail.google.com/"
            )

        self._gmail_client = GmailClientWrapper(
            _creds=convert_google_cred_to_oauth2_cred(self._creds)
        )
        await super().start()

    def _get_messages_from_ids(self, message_ids: List[str]) -> List[Message]:
        emails: List[Message] = []

        for message_id in message_ids:
            try:
                emails.append(self._gmail_client.get_message_by_id(message_id))
            except HttpError:
                pass

        return emails

    @staticmethod
    def _message_to_string(message: Message) -> str:
        return (
            dedent(
                f"""
            Message ID: {message.id}
            Thread ID: {message.thread_id}
            Sender ID: {message.headers.get('Message-ID', message.id)}
            From: {message.sender}
            To: {message.recipient}
            Subject: {message.subject}
            """
            )
            + f"Content: {message.plain or message.html}"
        )

    @function
    def add_labels(self, message_ids: List[str], labels: List[str]) -> str:
        """
        Add labels to the related emails in the previous chat.
        If the target email is not provided, you should search for it first.

        Args:
            message_ids: A list of IDs of messages that should be labeled. You can find this in the "Message ID: ..." line of the email.
            labels: A list of labels to add.
        """
        messages = self._get_messages_from_ids(message_ids)

        if len(messages) == 0:
            raise Exception("Error: No messages found for the given IDs")

        label_name_map = {
            label.name: label for label in self._gmail_client.list_labels()
        }
        labels_to_add = []

        for lbl in labels:
            if lbl not in label_name_map:
                new_label = self._gmail_client.create_label(lbl)
                label_name_map[lbl] = new_label
            labels_to_add.append(label_name_map[lbl])

        for msg in messages:
            self._gmail_client.add_labels(msg, labels_to_add)

        return "Labels added"

    @function
    def remove_labels(self, message_ids: List[str], labels: List[str]) -> str:
        """
        Remove labels from the related emails in the previous chat.
        If the target email is not provided, you should search for it first.

        Args:
            message_ids: A list of IDs of messages that should be labeled. You can find this in the "Message ID: ..." line of the email.
            labels: A list of labels to remove.
        """
        messages = self._get_messages_from_ids(message_ids)

        if len(messages) == 0:
            raise Exception("Error: No messages found for the given IDs")

        label_name_map = {
            label.name: label for label in self._gmail_client.list_labels()
        }
        labels_to_remove = []

        for lbl in labels:
            if lbl in label_name_map:
                labels_to_remove.append(label_name_map[lbl])

        if len(labels_to_remove):
            for msg in messages:
                self._gmail_client.remove_labels(msg, labels_to_remove)

        return "Labels removed"

    @function
    def create_draft(
        self,
        to: str,
        subject: str,
        message: str = None,
        cc: List[str] = None,
        bcc: List[str] = None,
    ) -> str:
        """
        Create an email draft.

        Args:
            to: The email address the message being sent to.
            subject: The subject line of the email.
            message: The email content in Markdown format.
            cc: The list of email addresses to cc.
            bcc: The list of email addresses to bcc.
        """
        msg = self._gmail_client.create_draft(
            sender="",
            to=to,
            cc=cc,
            bcc=bcc,
            subject=subject,
            msg_plain=message,
            msg_html=markdown(message),
        )

        return "The following draft is created:\n" + self._message_to_string(msg)

    @function
    def create_reply_draft(
        self,
        to: str,
        subject: str,
        recipient_id: str,
        message: str = None,
        cc: List[str] = None,
        bcc: List[str] = None,
    ):
        """
        Create a draft that replies to the last email retrieved in the previous chat.
        If the target email is not provided, you should search for it first.

        Args:
            to: The email address the message being sent to.
            subject: The subject line of the email.
            recipient_id: The ID of the recipient being replied to. You can find this in the "Sender ID: ..." line of the email.
            message: The reply message in Markdown format. You should also quote the email being replied to.
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
            cc: The list of email addresses to cc.
            bcc: The list of email addresses to bcc.
        """
        msg = self._gmail_client.create_draft(
            sender="",
            to=to,
            cc=cc,
            bcc=bcc,
            subject=subject,
            msg_plain=message,
            msg_html=markdown(message),
            reply_to=recipient_id,
        )

        return "The following reply draft is created:\n" + self._message_to_string(msg)

    @function
    def reply(
        self,
        to: str,
        subject: str,
        recipient_id: str,
        message: str = None,
        cc: List[str] = None,
        bcc: List[str] = None,
    ):
        """
        Reply to the last email retrieved in the previous chat.
        If the target email is not provided, you should search for it first.

        Args:
            to: The email address the message being sent to.
            subject: The subject line of the email.
            recipient_id: The ID of the recipient being replied to. You can find this in the "Sender ID: ..." line of the email.
            message: The reply message in Markdown format. You should also quote the email being replied to.
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
            cc: The list of email addresses to cc.
            bcc: The list of email addresses to bcc.
        """
        msg = self._gmail_client.send_message(
            sender="",
            to=to,
            cc=cc,
            bcc=bcc,
            subject=subject,
            msg_plain=message,
            msg_html=markdown(message),
            reply_to=recipient_id,
        )

        return "The following reply is sent:\n" + self._message_to_string(msg)

    @function
    def search_emails(self, query: str = None, max_results: int = 100) -> str:
        """
        Search for emails with a query.

        Args:
            query: A Gmail query to match emails.
            max_results: Maximum number of results to return.
        """
        msgs = self._gmail_client.get_messages(
            query=query,
            max_results=max_results,
        )

        return json.dumps(
            [self._message_to_string(m) for m in msgs], ensure_ascii=False
        )

    @function
    async def send_email(
        self,
        ctx: Context,
        to: str,
        subject: str,
        message: str = None,
        cc: List[str] = None,
        bcc: List[str] = None,
    ):
        """
        Send an email.

        Args:
            ctx: NPi context
            to: The email address the message being sent to.
            subject: The subject line of the email.
            message: The email content in Markdown format.
            cc: The list of email addresses to cc.
            bcc: The list of email addresses to bcc.
        """
        # approved = await self.hitl.confirm(
        #     ctx=ctx,
        #     tool_name=self.name,
        #     message=f'The following email will be sent to {to}:\n {message}'
        # )
        #
        # if not approved:
        #     return 'The email could not be sent due to user rejection'

        msg = self._gmail_client.send_message(
            sender="",
            to=to,
            cc=cc,
            bcc=bcc,
            subject=subject,
            msg_plain=message,
            msg_html=markdown(message),
        )

        return "Sending Success\n" + self._message_to_string(msg)

    @function
    async def wait_for_reply(self, sender: str):
        """
        Wait for reply from the last email sent in the previous chats.

        Args:
            sender: The reply message sender. This should be the recipient of the last email, and you can find it in the "To: ..." line.
        """
        while True:
            messages = self._gmail_client.get_messages(
                query=f"is:unread from:{sender}",
                max_results=1,
            )

            if len(messages):
                msg = messages[0]
                msg.mark_as_read()
                return self._message_to_string(msg)

            await asyncio.sleep(3)
