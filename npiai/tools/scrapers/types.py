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


class Row(TypedDict):
    hash: str
    original_data_index: int
    row_no: int
    values: Dict[str, str]


class RowBatch(TypedDict):
    # row offset of this batch in the entire task
    offset: int
    batch_id: int
    items: List[Row]
