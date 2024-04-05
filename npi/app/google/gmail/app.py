import json
import time
from typing import override
from markdown import markdown
from openai import OpenAI
from simplegmail.message import Message
from googleapiclient.errors import HttpError
from npi.core.api import App, FunctionRegistration
from .gmail_extended import GmailExtended
from .schema import *


class Gmail(App):
    gmail_client: GmailExtended

    def __init__(self, llm=None):
        super().__init__(
            name='gmail',
            description='interact with Gmail using English, e.g., gmail("send an email to test@gmail.com")',
            system_role='You are a Gmail Agent helping users to manage their emails',
            llm=llm or OpenAI(),
        )

        self.gmail_client = GmailExtended(client_secret_file='./credentials.json')

    def get_functions(self) -> List[FunctionRegistration]:
        return [
            FunctionRegistration(
                fn=self.search_emails,
                Params=SearchEmailsParameter,
                description='Search for emails with a query'
            ),
            FunctionRegistration(
                fn=self.send_email,
                Params=SendEmailParameter,
                description='Send an email'
            ),
            FunctionRegistration(
                fn=self.reply,
                Params=ReplyParameter,
                description='Reply to the last email retrieved in the previous chat. If the target email is not provided, you should search for it first'
            ),
            FunctionRegistration(
                fn=self.create_draft,
                Params=CreateDraftParameter,
                description='Create an email draft'
            ),
            FunctionRegistration(
                fn=self.create_reply_draft,
                Params=CreateReplyDraftParameter,
                description='Create a draft that replies to the last email retrieved in the previous chat. If the target email is not provided, you should search for it first'
            ),
            FunctionRegistration(
                fn=self.add_labels,
                Params=AddLabelsParameter,
                description='Add labels to the related emails in the previous chat. If the target email is not provided, you should search for it first'
            ),
            FunctionRegistration(
                fn=self.remove_labels,
                Params=AddLabelsParameter,
                description='Remove labels from the related emails in the previous chat. If the target email is not provided, you should search for it first'
            ),
            FunctionRegistration(
                fn=self.wait_for_reply,
                Params=WaitForReplyParameter,
                description='Wait for reply from the last email sent in the previous chat'
            ),
        ]

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

    def add_labels(self, params: AddLabelsParameter) -> str:
        messages = self._get_messages_from_ids(params.message_ids)

        if len(messages) == 0:
            return 'Error: No messages found for the given IDs'

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

    def remove_labels(self, params: RemoveLabelsParameter):
        messages = self._get_messages_from_ids(params.message_ids)

        if len(messages) == 0:
            return 'Error: No messages found for the given IDs'

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

    def create_draft(self, params: CreateDraftParameter):
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

    def create_reply_draft(self, params: CreateReplyDraftParameter):
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

    def reply(self, params: ReplyParameter):
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

    def search_emails(self, params: SearchEmailsParameter):
        msgs = self.gmail_client.get_messages(
            query=params.query,
            max_results=params.max_results,
        )

        return json.dumps([self._message_to_string(m) for m in msgs])

    def send_email(self, params: SendEmailParameter):
        msg = self.gmail_client.send_message(
            sender='',
            to=params.to,
            cc=params.cc,
            bcc=params.bcc,
            subject=params.subject,
            msg_plain=params.message,
            msg_html=markdown(params.message),
        )

        print(self._message_to_string(msg))

        return 'The following message is sent:\n' + self._message_to_string(msg)

    def wait_for_reply(self, params: WaitForReplyParameter):
        while True:
            messages = self.gmail_client.get_messages(
                query=f'is:unread from:{params.sent_from}',
                max_results=1,
            )

            if len(messages):
                msg = messages[0]
                msg.mark_as_read()
                return self._message_to_string(msg)

            time.sleep(3)
