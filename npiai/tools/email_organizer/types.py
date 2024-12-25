from typing import Literal, Dict
from typing_extensions import TypedDict, Annotated

from npiai.tools.shared_types.base_email_tool import EmailMessage


class FilterResult(TypedDict):
    matched: bool
    email: EmailMessage


class EmailSummary(TypedDict):
    id: str
    values: Dict[str, str]


class Column(TypedDict):
    name: Annotated[str, "Name of the column"]
    type: Annotated[Literal["text", "number"], "Type of the column"]
    description: Annotated[str, "A brief description of the column"]
    prompt: Annotated[
        str | None, "A step-by-step prompt on how to extract the column data"
    ]
