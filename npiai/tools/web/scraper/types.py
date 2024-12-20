from dataclasses import dataclass
from typing import List, Dict, Literal

from typing_extensions import TypedDict, Annotated

ScrapingType = Literal["single", "list-like"]


class Column(TypedDict):
    name: Annotated[str, "Name of the column"]
    type: Annotated[Literal["text", "link", "image"], "Type of the column"]
    description: Annotated[str, "A brief description of the column"]
    prompt: Annotated[
        str | None, "A step-by-step prompt on how to extract the column data"
    ]


class SummaryItem(TypedDict):
    hash: str
    values: Dict[str, str]


class SummaryChunk(TypedDict):
    batch_id: int
    matched_hashes: List[str]
    items: List[SummaryItem]


@dataclass
class ConversionResult:
    markdown: str
    hashes: List[str]
    matched_hashes: List[str]
