import asyncio
import json

from googleapiclient.errors import HttpError
from markdown import markdown
from npiai_proto import api_pb2
from simplegmail.message import Message

from npi.config import config
from npi.error.auth import UnauthorizedError
from npi.app.google import GoogleApp
from npi.core.app import npi_tool, callback
from npi.utils import logger
from .client import GmailClientWrapper
from .schema import *

from google.oauth2.credentials import Credentials
from oauth2client.client import OAuth2Credentials, GoogleCredentials


def convert_credentials(google_credentials: Credentials) -> OAuth2Credentials:
    return OAuth2Credentials(
        access_token=None,
        client_id=google_credentials._client_id,
        client_secret=google_credentials._client_secret,
        refresh_token=google_credentials._refresh_token,
        token_expiry=google_credentials.expiry,
        token_uri=google_credentials._token_uri,
        user_agent=None
    )


class Gmail(GoogleApp):
    gmail_client: GmailClientWrapper

    SCOPE = ["https://mail.google.com/"]

    def __init__(self, llm=None):
        cred = config.get_gmail_credentials()
        if cred is None:
            raise UnauthorizedError("Gmail credentials not found, please use `npi auth google gmail` first")
        super().__init__(
            name='gmail',
            description='interact with Gmail using English, e.g., gmail("send an email to test@gmail.com")',
            system_role='You are a Gmail Agent helping users to manage their emails',
            llm=llm,
            creds=cred.token,
            scopes=[
                "https://mail.google.com/"
            ],
        )

        self.gmail_client = GmailClientWrapper(
            _creds=convert_credentials(self._get_creds()),
        )

    def _get_messages_from_ids(self, message_ids: List[str]) -> List[Message]:
        emails: List[Message] = []

        for message_id in message_ids:
            try:
                emails.append(self.gmail_client.get_message_by_id(message_id))
            except HttpError:
                pass

        return emails

    @staticmethod
    def _message_to_string(message: Message) -> str:
        return dedent(
            f"""
            Message ID: {message.id}
            Thread ID: {message.thread_id}
            Sender ID: {message.headers.get('Message-ID', message.id)}
            From: {message.sender}
            To: {message.recipient}
            Subject: {message.subject}
            """
        ) + f"Content: {message.plain or message.html}"

    @npi_tool
    def add_labels(self, params: AddLabelsParameters) -> str:
        """
        Add labels to the related emails in the previous chat.
        If the target email is not provided, you should search for it first.
        """
        messages = self._get_messages_from_ids(params.message_ids)

        if len(messages) == 0:
            raise Exception('Error: No messages found for the given IDs')

        labels = self.gmail_client.list_labels()
        label_name_map = {label.name: label for label in labels}
        labels_to_add = []

        for lbl in params.labels:
            if lbl not in label_name_map:
                new_label = self.gmail_client.create_label(lbl)
                label_name_map[lbl] = new_label
            labels_to_add.append(label_name_map[lbl])

        for msg in messages:
            self.gmail_client.add_labels(msg, labels_to_add)

        return 'Labels added'

    @npi_tool
    def remove_labels(self, params: RemoveLabelsParameters):
        """
        Remove labels from the related emails in the previous chat.
        If the target email is not provided, you should search for it first.
        """
        messages = self._get_messages_from_ids(params.message_ids)

        if len(messages) == 0:
            raise Exception('Error: No messages found for the given IDs')

        labels = self.gmail_client.list_labels()
        label_name_map = {label.name: label for label in labels}
        labels_to_remove = []

        for lbl in params.labels:
            if lbl in label_name_map:
                labels_to_remove.append(label_name_map[lbl])

        if len(labels_to_remove):
            for msg in messages:
                self.gmail_client.remove_labels(msg, labels_to_remove)

        return 'Labels removed'

    @npi_tool
    def create_draft(self, params: CreateDraftParameter):
        """Create an email draft"""
        msg = self.gmail_client.create_draft(
            sender='',
            to=params.to,
            cc=params.cc,
            bcc=params.bcc,
            subject=params.subject,
            msg_plain=params.message,
            msg_html=markdown(params.message),
        )

        return 'The following draft is created:\n' + self._message_to_string(msg)

    @npi_tool
    def create_reply_draft(self, params: CreateReplyDraftParameter):
        """
        Create a draft that replies to the last email retrieved in the previous chat.
        If the target email is not provided, you should search for it first.
        """
        msg = self.gmail_client.create_draft(
            sender='',
            to=params.to,
            cc=params.cc,
            bcc=params.bcc,
            subject=params.subject,
            msg_plain=params.message,
            msg_html=markdown(params.message),
            reply_to=params.recipient_id,
        )

        return 'The following reply draft is created:\n' + self._message_to_string(msg)

    @npi_tool
    def reply(self, params: ReplyParameter):
        """
        Reply to the last email retrieved in the previous chat.
        If the target email is not provided, you should search for it first.
        """
        msg = self.gmail_client.send_message(
            sender='',
            to=params.to,
            cc=params.cc,
            bcc=params.bcc,
            subject=params.subject,
            msg_plain=params.message,
            msg_html=markdown(params.message),
            reply_to=params.recipient_id,
        )

        return 'The following reply is sent:\n' + self._message_to_string(msg)

    @npi_tool
    def search_emails(self, params: SearchEmailsParameters):
        """Search for emails with a query"""
        msgs = self.gmail_client.get_messages(
            query=params.query,
            max_results=params.max_results,
        )

        return json.dumps([self._message_to_string(m) for m in msgs])

    @npi_tool
    async def send_email(self, params: SendEmailParameters):
        """Send an email"""
        cb = callback.Callable(
            action=api_pb2.ActionRequiredResponse(
                type=api_pb2.ActionType.CONFIRMATION,
                # TODO(wenfeng) use structured message
                message=f"following is the email content will be sent to {params.to}, please confirm:\n{params.message}",
            ),
        )
        cb.action.action_id = cb.id()
        await params.get_thread().send_msg(cb=cb)  # TODO(wenfeng) how to save state and then recover?
        logger.info(f"Waiting for user approving...")
        response = await cb.wait()  # TODO(wenfeng) return hangup and recovery later
        if not response.is_approved():
            if response.has_message():
                return f"sending denied, reason: {response}, then please try again,"
            else:
                # TODO(wenfeng) use structured response to exist?
                return f"sending denied, reason: user denied, please exit processing"

        _ = self.gmail_client.send_message(
            sender='',
            to=params.to,
            cc=params.cc,
            bcc=params.bcc,
            subject=params.subject,
            msg_plain=params.message,
            msg_html=markdown(params.message),
        )

        return 'Sending Success\n'  # + self._message_to_string(msg)

    @npi_tool
    async def wait_for_reply(self, params: WaitForReplyParameters):
        """Wait for reply from the last email sent in the previous chats"""
        while True:
            messages = self.gmail_client.get_messages(
                query=f'is:unread from:{params.sent_from}',
                max_results=1,
            )

            if len(messages):
                msg = messages[0]
                msg.mark_as_read()
                return self._message_to_string(msg)

            await asyncio.sleep(3)
