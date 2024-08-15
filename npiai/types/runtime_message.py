from typing import TypedDict, Literal


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


class HITLMessage(TypedDict):
    type: Literal["hitl"]
    id: str
    action: Literal["input", "confirm"]
    message: str


class ScreenshotMessage(TypedDict):
    type: Literal["screenshot"]
    id: str
    screenshot: str


RuntimeMessage = (
    ToolMessage
    | ExecutionResultMessage
    | DebugMessage
    | HITLMessage
    | ScreenshotMessage
)
