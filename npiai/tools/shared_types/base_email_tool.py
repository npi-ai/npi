from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, TypedDict


class EmailMessage(TypedDict):
    id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    body: str | None
    cc: list[str] | None
    bcc: list[str] | None


class EmailAttachment(TypedDict):
    id: str
    message_id: str
    filename: str
    filetype: str
    data: bytes | None


class BaseEmailTool(ABC):
    @abstractmethod
    async def list_inbox_stream(
        self,
        limit: int = 10,
        query: str = None,
    ) -> AsyncGenerator[EmailMessage, None]:
        pass

    @abstractmethod
    async def get_message_by_id(self, message_id: str) -> EmailMessage | None:
        pass

    @abstractmethod
    async def download_attachments_in_message(
        self,
        message_id: str,
        filter_by_type: str = None,
    ) -> List[EmailAttachment] | None:
        pass
