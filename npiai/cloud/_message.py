from typing import TypedDict, Literal, Dict, Any


class ActionResultMessage(TypedDict):
    type: Literal["action_result"]
    action_id: str
    result: str


class ToolCallMessage(TypedDict):
    type: Literal["tool_call"]
    tool_call_id: str
    tool_name: str
    arguments: Dict[str, Any]


WSClientMessage = ActionResultMessage | ToolCallMessage
