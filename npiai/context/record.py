import uuid
from dataclasses import dataclass, field
from typing import List, Any

from litellm.types.completion import ChatCompletionMessageParam
from litellm import ModelResponse

from datetime import datetime


@dataclass(frozen=True)
class Record:
    checkpoint: Any
    prompts: List[ChatCompletionMessageParam]
    response: ModelResponse
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now())
