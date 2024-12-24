from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator


@dataclass
class EmailMessage:
    id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    body: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None


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
