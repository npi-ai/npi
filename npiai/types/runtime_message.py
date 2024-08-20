from typing import TypedDict, Literal, List


class ToolMessage(TypedDict):
    type: Literal["message"]
    id: str
    message: str


class ExecutionResultMessage(TypedDict):
    type: Literal["execution_result"]
    id: str
    tool_call_id: str
    result: str


class DebugMessage(TypedDict):
    type: Literal["debug"]
    id: str
    message: str


class ErrorMessage(TypedDict):
    type: Literal["error"]
    id: str
    message: str


class HITLInputMessage(TypedDict):
    type: Literal["hitl"]
    id: str
    action: Literal["input"]
    message: str
    default: str


class HITLConfirmMessage(TypedDict):
    type: Literal["hitl"]
    id: str
    action: Literal["input"]
    message: str
    default: bool


class HITLSelectMessage(TypedDict):
    type: Literal["hitl"]
    id: str
    action: Literal["select"]
    message: str
    choices: List[str]
    default: str


class ScreenshotMessage(TypedDict):
    type: Literal["screenshot"]
    id: str
    screenshot: str


HITLMessage = HITLInputMessage | HITLConfirmMessage | HITLSelectMessage

RuntimeMessage = (
    ToolMessage
    | ExecutionResultMessage
    | DebugMessage
    | HITLMessage
    | ScreenshotMessage
)
