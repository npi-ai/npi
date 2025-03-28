import asyncio
import json
from typing import AsyncGenerator, List, cast

import pymupdf
from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from typing_extensions import TypedDict

from npiai import Context
from npiai.tools.shared_types.base_email_tool import BaseEmailTool, EmailMessage
from npiai.utils import llm_tool_call, concurrent_task_runner
from npiai.tools.scrapers import BaseScraper, SourceItem
from .prompts import FILTER_PROMPT
from .types import FilterResult


class CompactAttachment(TypedDict):
    filename: str
    content: str | None


class CompactEmailMessage(EmailMessage):
    attachments: List[CompactAttachment] | None


class EmailOrganizer(BaseScraper):
    name = "email_organizer"
    description = "An email agent that helps users organize their emails"
    system_prompt = (
        "You are an email organizer agent helping user organize their emails."
    )

    _provider: BaseEmailTool
    _email_or_id_list: List[EmailMessage] | List[str]
    _with_pdf_attachments: bool

    _email_map: dict[str, EmailMessage]

    # current reading email index
    _current_index: int = 0

    # lock to increase current reading email index
    _read_email_lock: asyncio.Lock

    def __init__(
        self,
        provider: BaseEmailTool,
        email_or_id_list: List[EmailMessage] | List[str],
        with_pdf_attachments: bool = False,
    ):
        super().__init__()
        self._provider = provider
        self._email_or_id_list = email_or_id_list
        self._email_map = {email["id"]: email for email in self._email_or_id_list}
        self._with_pdf_attachments = with_pdf_attachments
        self._read_email_lock = asyncio.Lock()

    async def start(self):
        await self._provider.start()

    async def end(self):
        await self._provider.end()

    async def init_data(self, ctx: Context):
        async with self._read_email_lock:
            self._current_index = 0

    async def next_items(self, ctx: Context, count: int) -> List[SourceItem] | None:
        items = []

        for i in range(count):
            async with self._read_email_lock:
                if self._current_index >= len(self._email_or_id_list):
                    return items

                email = self._email_or_id_list[self._current_index]
                self._current_index += 1

            if isinstance(email, str):
                email = await self._provider.get_message_by_id(email)

            if not email:
                continue

            if self._with_pdf_attachments:
                compact_email = await self._to_compact_email_with_pdf_attachments(email)
            else:
                compact_email = self._to_compact_email(email)

            # remove id and thread_id to avoid showing up in summary
            data = cast(dict, compact_email)

            data.pop("id", None)
            data.pop("thread_id", None)

            items.append(
                SourceItem(
                    hash=email["id"],
                    data=data,
                )
            )

        return items

    async def filter_stream(
        self,
        ctx: Context,
        criteria: str,
        concurrency: int = 1,
    ) -> AsyncGenerator[FilterResult, None]:
        """
        Filter emails based on specific criteria

        Args:
            ctx: NPi Context
            criteria: Filtering criteria
            concurrency: Number of concurrent filtering tasks
        """

        async def process_email(results_queue: asyncio.Queue[FilterResult]):
            emails = await self.next_items(ctx, 1)

            if not emails:
                return

            res = await self._filter_llm_call(ctx, emails[0]["data"], criteria)
            await results_queue.put(res)

            await process_email(results_queue)

        async for result in concurrent_task_runner(process_email, concurrency):
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

        async def callback(matched: bool):
            """
            Callback function to determine whether the email meets the filtering criteria

            Args:
                matched: Whether the email meets the filtering criteria
            """
            return FilterResult(
                matched=matched,
                email=self._email_map[email["id"]],
            )

        return await llm_tool_call(
            ctx=ctx,
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

        pdf_attachments = []

        for attachment in email["attachments"]:
            if attachment["filetype"] != "application/pdf":
                continue

            data = attachment["data"]

            if not data:
                data = await self._provider.download_attachment(
                    message_id=attachment["message_id"],
                    attachment_id=attachment["id"],
                )

            if not data:
                continue

            doc = pymupdf.open(stream=data, filetype="pdf")
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
