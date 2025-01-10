from typing_extensions import TypedDict

from npiai.tools.shared_types.base_email_tool import EmailMessage


class FilterResult(TypedDict):
    matched: bool
    email: EmailMessage
