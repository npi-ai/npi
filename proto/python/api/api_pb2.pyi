from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import wrappers_pb2 as _wrappers_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RequestCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    REQUEST_UNKNOWN: _ClassVar[RequestCode]
    CHAT: _ClassVar[RequestCode]
    FETCH: _ClassVar[RequestCode]
    ACTION_RESULT: _ClassVar[RequestCode]

class ResponseCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RESPONSE_UNKNOWN: _ClassVar[ResponseCode]
    SUCCESS: _ClassVar[ResponseCode]
    FAILED: _ClassVar[ResponseCode]
    MESSAGE: _ClassVar[ResponseCode]
    HUMAN_FEEDBACK: _ClassVar[ResponseCode]
    CLIENT_ACTION: _ClassVar[ResponseCode]

class AppType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    APP_UNKNOWN: _ClassVar[AppType]
    GOOGLE_GMAIL: _ClassVar[AppType]
    GOOGLE_CALENDAR: _ClassVar[AppType]
    GITHUB: _ClassVar[AppType]
    SLACK: _ClassVar[AppType]
    DISCORD: _ClassVar[AppType]
    TWITTER: _ClassVar[AppType]
REQUEST_UNKNOWN: RequestCode
CHAT: RequestCode
FETCH: RequestCode
ACTION_RESULT: RequestCode
RESPONSE_UNKNOWN: ResponseCode
SUCCESS: ResponseCode
FAILED: ResponseCode
MESSAGE: ResponseCode
HUMAN_FEEDBACK: ResponseCode
CLIENT_ACTION: ResponseCode
APP_UNKNOWN: AppType
GOOGLE_GMAIL: AppType
GOOGLE_CALENDAR: AppType
GITHUB: AppType
SLACK: AppType
DISCORD: AppType
TWITTER: AppType

class Request(_message.Message):
    __slots__ = ("code", "request_id", "thread_id", "chat_request", "action_result_request", "empty")
    CODE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    THREAD_ID_FIELD_NUMBER: _ClassVar[int]
    CHAT_REQUEST_FIELD_NUMBER: _ClassVar[int]
    ACTION_RESULT_REQUEST_FIELD_NUMBER: _ClassVar[int]
    EMPTY_FIELD_NUMBER: _ClassVar[int]
    code: RequestCode
    request_id: str
    thread_id: str
    chat_request: ChatRequest
    action_result_request: ActionResultRequest
    empty: _empty_pb2.Empty
    def __init__(self, code: _Optional[_Union[RequestCode, str]] = ..., request_id: _Optional[str] = ..., thread_id: _Optional[str] = ..., chat_request: _Optional[_Union[ChatRequest, _Mapping]] = ..., action_result_request: _Optional[_Union[ActionResultRequest, _Mapping]] = ..., empty: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ("code", "request_id", "thread_id", "chat_response", "empty")
    CODE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    THREAD_ID_FIELD_NUMBER: _ClassVar[int]
    CHAT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    EMPTY_FIELD_NUMBER: _ClassVar[int]
    code: ResponseCode
    request_id: str
    thread_id: str
    chat_response: ChatResponse
    empty: _empty_pb2.Empty
    def __init__(self, code: _Optional[_Union[ResponseCode, str]] = ..., request_id: _Optional[str] = ..., thread_id: _Optional[str] = ..., chat_response: _Optional[_Union[ChatResponse, _Mapping]] = ..., empty: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ...) -> None: ...

class ChatRequest(_message.Message):
    __slots__ = ("app_type", "instruction")
    APP_TYPE_FIELD_NUMBER: _ClassVar[int]
    INSTRUCTION_FIELD_NUMBER: _ClassVar[int]
    app_type: AppType
    instruction: str
    def __init__(self, app_type: _Optional[_Union[AppType, str]] = ..., instruction: _Optional[str] = ...) -> None: ...

class ChatResponse(_message.Message):
    __slots__ = ("thread_id", "message")
    THREAD_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    thread_id: str
    message: str
    def __init__(self, thread_id: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class ActionResultRequest(_message.Message):
    __slots__ = ("action_id", "action_result")
    ACTION_ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_RESULT_FIELD_NUMBER: _ClassVar[int]
    action_id: str
    action_result: str
    def __init__(self, action_id: _Optional[str] = ..., action_result: _Optional[str] = ...) -> None: ...
