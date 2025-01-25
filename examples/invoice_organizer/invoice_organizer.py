import json
import os
from textwrap import dedent

from simplegmail.message import Message
from google.oauth2.credentials import Credentials as GoogleCredentials
from markdownify import markdownify

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from npiai import FunctionTool, Context, function
from npiai.error import UnauthorizedError
from npiai.utils import logger

from gmail_client import GmailClient
from invoice_processor import InvoiceProcessor
from constants import StorageKeys
from output_configs import OutputConfigs
from search_query_configs import SearchQueryConfigs


class InvoiceOrganizer(FunctionTool):
    name = "invoice_organizer"

    description = "Search for invoices in gmail messages and organize them"

    system_prompt = dedent(
        """
        You are an agent helping user identify and organize invoice-like emails in
        Gmail inbox. For any given instruction, you should call the `organize_invoices` 
        tool to process the emails.
        """
    )

    _gmail_client: GmailClient
    _creds: GoogleCredentials
    _processor: InvoiceProcessor

    def __init__(self, creds: GoogleCredentials | None = None):
        super().__init__()
        self._processor = InvoiceProcessor()

        if creds:
            self._creds = creds
        else:
            cred_file = os.environ.get("GOOGLE_CREDENTIAL")

            if cred_file is None:
                raise UnauthorizedError("Google credential file not found")

            self._creds = GoogleCredentials.from_authorized_user_file(
                filename=cred_file, scopes="https://mail.google.com/"
            )

    async def start(self):
        self._gmail_client = GmailClient(self._creds)
        await super().start()

    @function
    async def organize_invoices(self, ctx: Context):
        """
        Search for invoice-like Gmail messages and organize them

        Args:
            ctx: NPi Context
        """
        query = await ctx.kv.get(StorageKeys.QUERY)

        processed_messages = []

        for message in self._gmail_client.search_iterator(query=query):
            processed = await self._identify_invoice_message(ctx, message)

            if processed:
                processed_messages.append(
                    {
                        "subject": message.subject,
                        "sender": message.sender,
                        "date": message.date,
                    }
                )

        return dedent(
            f"""
            Processed {len(processed_messages)} messages:
            {json.dumps(processed_messages, ensure_ascii=False)}
            """
        )

    async def _identify_invoice_message(self, ctx: Context, message: Message):
        prompts = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=dedent(
                    """
                    As an AI agent, your task is to analyze each email to determine if it is an 
                    invoice-related email. For emails that are invoice-related:

                    1. Identify and extract key information such as the `assigner` (the entity 
                       sending the invoice) and the `date` (when the invoice was issued).
                    2. After extracting the relevant information, use the `process_invoice` tool 
                       to handle the invoice accordingly.
                    
                    For emails that are not related to invoices, take no action. Ensure that your 
                    response includes any extracted information if applicable. Prioritize accuracy 
                    in identifying and extracting details from invoice emails.
                    """
                ),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                # TODO: parse the attachments?
                content=dedent(
                    f"""
                    Subject: {message.subject}
                    Date: {message.date}
                    From: {message.sender}
                    To: {message.recipient}
                    
                    Content:
                    {message.plain or markdownify(message.html)}
                    """
                ),
            ),
        ]

        response = await ctx.llm.acompletion(
            messages=prompts,
            tools=self._processor.tools,
            tool_choice="auto",
            max_tokens=4096,
        )

        response_message = response.choices[0].message
        tool_calls = response_message.get("tool_calls", None)

        if response_message.content:
            logger.debug(
                f"Email: {message.subject}\nResponse: {response_message.content}"
            )

        if tool_calls:
            await self._processor.call(
                tool_calls=tool_calls,
                session=ctx,
            )

            return True

        return False


if __name__ == "__main__":
    import asyncio
    from npiai import agent, OpenAI
    from npiai.hitl_handler import ConsoleHandler

    from debug_context import DebugContext

    async def main():
        llm = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", None),
            model="gpt-4o",
        )

        ctx = DebugContext()
        ctx.use_hitl(ConsoleHandler())
        ctx.use_llm(llm)
        ctx.use_configs(
            SearchQueryConfigs(),
            OutputConfigs(),
        )

        async with agent.wrap(InvoiceOrganizer()) as organizer:
            await organizer.chat(
                ctx, "summarize invoices in the past 3 month and save as invoices.json"
            )

    asyncio.run(main())
