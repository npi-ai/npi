import json
from typing import AsyncGenerator

from azure.core.credentials import TokenCredential
from markdown import markdown
from msgraph import GraphServiceClient
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.message import Message
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
    MessagesRequestBuilder,
)
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody,
)

from npiai import FunctionTool, function, Context
from npiai.utils import html_to_markdown
from npiai.tools.shared_types.base_email_tool import BaseEmailTool, EmailMessage


class Outlook(FunctionTool, BaseEmailTool):
    name = "outlook"
    description = "Manage Outlook emails"
    system_prompt = "You are an agent helping user manage Outlook emails."

    _creds: TokenCredential
    _client: GraphServiceClient

    def __init__(self, creds: TokenCredential):
        super().__init__()
        self._creds = creds
        self._client = GraphServiceClient(
            credentials=creds,
            scopes=["Mail.Read", "Mail.Send"],
        )

    def _get_email_address(self, recipient: Recipient) -> str:
        if not recipient.email_address:
            return ""

        return f"{recipient.email_address.name} <{recipient.email_address.address}>"

    def convert_message(self, message: Message):
        recipients = ", ".join(
            self._get_email_address(recipient) for recipient in message.to_recipients
        )

        return EmailMessage(
            id=message.id,
            thread_id=message.conversation_id,
            sender=self._get_email_address(message.sender),
            recipient=recipients,
            subject=message.subject,
            body=html_to_markdown(message.body.content) if message.body else None,
        )

    async def get_message_by_id(self, message_id: str):
        """
        Get a message by its ID

        Args:
            message_id: the ID of the message
        """
        msg = await self._client.me.messages.by_message_id(message_id).get()
        return self.convert_message(msg)

    async def list_inbox_stream(
        self, limit: int = -1, query: str = None
    ) -> AsyncGenerator[EmailMessage, None]:
        """
        List emails in the inbox

        Args:
            limit: The number of emails to list, -1 for all. Default is -1.
            query: A query to filter the emails. Default is None.
        """
        page_size = 10 if limit == -1 else min(limit, 10)
        select = ["id", "subject", "from", "receivedDateTime", "body"]
        count = 0

        while limit == -1 or count < limit:
            query_params = (
                MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
                    skip=count,
                    top=page_size,
                    search=query,
                    select=select,
                    orderby=["receivedDateTime DESC"],
                )
            )

            request_config = (
                MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
                    query_parameters=query_params,
                )
            )

            messages = await self._client.me.messages.get(
                request_configuration=request_config,
            )

            if not messages:
                return

            for message in messages.value:
                yield self.convert_message(message)
                count += 1

                if limit != -1 and count >= limit:
                    return

    @function
    async def search_emails(
        self,
        limit: int = 100,
        query: str = None,
    ) -> str:
        """
        Search for emails with a query.

        Args:
            limit: The number of emails to return, -1 for all. Default is -1.
            query: A query to filter the emails. Default is None.
        """
        messages = []

        async for msg in self.list_inbox_stream(
            limit=limit,
            query=query,
        ):
            messages.append(msg)

        return json.dumps(messages, ensure_ascii=False)

    @function
    async def send_email(
        self,
        ctx: Context,
        to: str,
        subject: str,
        message: str = None,
        cc: list[str] = None,
        bcc: list[str] = None,
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
        approved = await ctx.hitl.confirm(
            tool_name=self.name,
            message=f"Continue sending the following email to {to}?\n{message}",
        )

        if not approved:
            return "The email could not be sent due to user rejection"

        body = ItemBody(
            content_type=BodyType.Html,
            content=markdown(message or ""),
        )

        recipient = Recipient(
            email_address=EmailAddress(
                address=to,
            ),
        )

        cc_recipients = [
            Recipient(
                email_address=EmailAddress(
                    address=cc_address,
                ),
            )
            for cc_address in cc or []
        ]

        bcc_recipients = [
            Recipient(
                email_address=EmailAddress(
                    address=bcc_address,
                ),
            )
            for bcc_address in bcc or []
        ]

        message = Message(
            subject=subject,
            body=body,
            to_recipients=[recipient],
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
        )

        request_body = SendMailPostRequestBody(
            message=message,
        )

        await self._client.me.send_mail.post(body=request_body)

        # TODO: get the message ID and return it

        return "Email sent successfully"
