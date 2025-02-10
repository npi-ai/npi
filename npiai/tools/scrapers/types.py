from typing import List, Dict, Literal, Any

from typing_extensions import TypedDict, Annotated


class Column(TypedDict):
    name: Annotated[str, "Name of the column"]
    type: Annotated[Literal["text", "number", "link", "image"], "Type of the column"]
    prompt: Annotated[
        str | None, "A step-by-step prompt on how to extract the column data"
    ]


class SourceItem(TypedDict):
    hash: str
    data: Any


class SummaryItem(TypedDict):
    hash: str
    index: int
    values: Dict[str, str]


class SummaryChunk(TypedDict):
    index: int
    batch_id: int
    items: List[SummaryItem]
