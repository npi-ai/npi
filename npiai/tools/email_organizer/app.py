import asyncio
import json
from typing import AsyncGenerator, List, cast, Literal

from typing_extensions import TypedDict, overload

import pymupdf
from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from npiai import FunctionTool, Context
from npiai.utils import llm_tool_call, concurrent_task_runner, llm_summarize
from npiai.tools.shared_types.base_email_tool import BaseEmailTool, EmailMessage

from .prompts import FILTER_PROMPT, SUMMARIZE_PROMPT
from .types import FilterResult, Column, EmailSummary


class CompactAttachment(TypedDict):
    filename: str
    content: str | None


class CompactEmailMessage(EmailMessage):
    attachments: List[CompactAttachment] | None


class EmailOrganizer(FunctionTool):
    name = "email_organizer"
    description = "An email agent that helps users organize their emails"
    system_prompt = (
        "You are an email organizer agent helping user organize their emails."
    )

    _provider: BaseEmailTool

    def __init__(self, provider: BaseEmailTool):
        super().__init__()
        self._provider = provider

    async def start(self):
        await self._provider.start()

    async def end(self):
        await self._provider.end()

    async def list_inbox_stream(
        self,
        limit: int = -1,
        query: str = None,
    ) -> AsyncGenerator[EmailMessage | CompactEmailMessage, None]:
        """
        List emails in the inbox

        Args:
            limit: The number of emails to list, -1 for all. Default is -1.
            query: A query to filter the emails. Default is None.
        """
        async for email in self._provider.list_inbox_stream(limit=limit, query=query):
            yield email

    async def filter_stream(
        self,
        ctx: Context,
        email_or_id_list: List[EmailMessage] | List[str],
        criteria: str,
        concurrency: int = 1,
    ) -> AsyncGenerator[FilterResult, None]:
        """
        Filter emails based on specific criteria

        Args:
            ctx: NPi Context
            email_or_id_list: List of emails or message IDs
            criteria: Filtering criteria
            concurrency: Number of concurrent filtering tasks
        """

        lock = asyncio.Lock()
        index = 0

        async def process_email(results_queue: asyncio.Queue[FilterResult]):
            nonlocal index
            async with lock:
                if index >= len(email_or_id_list):
                    return

                email = email_or_id_list[index]
                index += 1

            if isinstance(email, str):
                email = await self._provider.get_message_by_id(email)

            res = await self._filter_llm_call(ctx, email, criteria)
            await results_queue.put(res)

            await process_email(results_queue)

        async for result in concurrent_task_runner(process_email, concurrency):
            yield result

    async def summarize_stream(
        self,
        ctx: Context,
        email_or_id_list: List[EmailMessage] | List[str],
        output_columns: List[Column],
        with_pdf_attachments: bool = False,
        concurrency: int = 1,
    ):
        """
        Summarize emails into a table.

        Args:
            ctx: NPi Context
            email_or_id_list: List of emails or message IDs
            output_columns: Columns to include in the table
            with_pdf_attachments: Whether to include PDF attachments in the summary
            concurrency: Number of concurrent summarization tasks
        """
        lock = asyncio.Lock()
        index = 0

        async def summarize_email(results_queue: asyncio.Queue[FilterResult]):
            nonlocal index
            async with lock:
                if index >= len(email_or_id_list):
                    return

                email = email_or_id_list[index]
                index += 1

            if isinstance(email, str):
                email = await self._provider.get_message_by_id(email)

            if not email:
                await summarize_email(results_queue)
                return

            if with_pdf_attachments:
                email = await self._to_compact_email_with_pdf_attachments(email)
            else:
                email = self._to_compact_email(email)

            res = await self._summarize_llm_call(
                ctx, cast(CompactEmailMessage, email), output_columns
            )

            if res:
                await results_queue.put(res)

            await summarize_email(results_queue)

        async for result in concurrent_task_runner(summarize_email, concurrency):
            yield result

    async def _filter_llm_call(
        self,
        ctx: Context,
        email: EmailMessage,
        criteria: str,
    ) -> FilterResult:
        """
        Call the LLM model to filter the email

        Args:
            ctx: NPi Context
            email: Email to filter
            criteria: Filtering criteria
        """

        def callback(matched: bool):
            """
            Callback function to determine whether the email meets the filtering criteria

            Args:
                matched: Whether the email meets the filtering criteria
            """
            return FilterResult(
                matched=matched,
                email=email,
            )

        res = await llm_tool_call(
            llm=ctx.llm,
            tool=callback,
            messages=[
                ChatCompletionSystemMessageParam(role="system", content=FILTER_PROMPT),
                ChatCompletionUserMessageParam(
                    role="user",
                    content=json.dumps(
                        {
                            "criteria": criteria,
                            "email": email,
                        },
                        ensure_ascii=False,
                    ),
                ),
            ],
        )

        return callback(**res.model_dump())

    async def _summarize_llm_call(
        self,
        ctx: Context,
        email: CompactEmailMessage,
        output_columns: List[Column],
    ) -> EmailSummary | None:
        """
        Call the LLM model to summarize the email

        Args:
            ctx: NPi Context
            email: Email to summarize
            output_columns: Columns to include in the table
        """
        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=SUMMARIZE_PROMPT.format(
                    column_defs=json.dumps(output_columns, ensure_ascii=False)
                ),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=json.dumps(email, ensure_ascii=False),
            ),
        ]

        try:
            results = []

            async for row in llm_summarize(ctx.llm, messages):
                results.append(
                    EmailSummary(
                        id=email["id"],
                        values=row,
                    )
                )

            return results[0]
        except Exception as e:
            await ctx.send_error_message(
                f"[{self.name}] Error parsing the response: {str(e)}"
            )

            return None

    def _to_compact_email(self, email: EmailMessage) -> CompactEmailMessage:
        attachments = email.get("attachments", None)

        if attachments:
            attachments = [
                {
                    "filename": attachment["filename"],
                    "content": (
                        "<binary data>" if type(attachment["data"]) is bytes else None
                    ),
                }
                for attachment in attachments
            ]

        return cast(CompactEmailMessage, {**email, "attachments": attachments})

    async def _to_compact_email_with_pdf_attachments(
        self,
        email: EmailMessage,
    ) -> CompactEmailMessage:
        """
        Read PDF attachments from the email

        Args:
            email: Email with PDF attachments
        """
        if not email["attachments"]:
            return cast(CompactEmailMessage, email)

        attachments = await self._provider.download_attachments_in_message(
            email["id"],
            filter_by_type="application/pdf",
        )

        if not attachments:
            return cast(CompactEmailMessage, {**email, "attachments": None})

        pdf_attachments = []

        for attachment in attachments:
            if not attachment["data"]:
                continue

            doc = pymupdf.open(stream=attachment["data"], filetype="pdf")
            content = ""

            for page in doc:
                content += page.get_text() + "\n\n"

            pdf_attachments.append(
                CompactAttachment(
                    filename=attachment["filename"],
                    content=content,
                )
            )

        return cast(
            CompactEmailMessage, {**email, "attachments": pdf_attachments or None}
        )
