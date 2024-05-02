from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RequestCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    REQUEST_UNKNOWN: _ClassVar[RequestCode]
    CHAT: _ClassVar[RequestCode]
    FETCH: _ClassVar[RequestCode]
    ACTION_RESULT: _ClassVar[RequestCode]

class AppType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    APP_UNKNOWN: _ClassVar[AppType]
    GOOGLE_GMAIL: _ClassVar[AppType]
    GOOGLE_CALENDAR: _ClassVar[AppType]
    GITHUB: _ClassVar[AppType]
    SLACK: _ClassVar[AppType]
    DISCORD: _ClassVar[AppType]
    TWITTER: _ClassVar[AppType]
    WEB_BROWSER: _ClassVar[AppType]

class ResponseCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RESPONSE_UNKNOWN: _ClassVar[ResponseCode]
    SUCCESS: _ClassVar[ResponseCode]
    FAILED: _ClassVar[ResponseCode]
    MESSAGE: _ClassVar[ResponseCode]
    ACTION_REQUIRED: _ClassVar[ResponseCode]
    FINISHED: _ClassVar[ResponseCode]

class ActionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_ACTION: _ClassVar[ActionType]
    INFORMATION: _ClassVar[ActionType]
    SINGLE_SELECTION: _ClassVar[ActionType]
    MULTIPLE_SELECTION: _ClassVar[ActionType]
    CONFIRMATION: _ClassVar[ActionType]
REQUEST_UNKNOWN: RequestCode
CHAT: RequestCode
FETCH: RequestCode
ACTION_RESULT: RequestCode
APP_UNKNOWN: AppType
GOOGLE_GMAIL: AppType
GOOGLE_CALENDAR: AppType
GITHUB: AppType
SLACK: AppType
DISCORD: AppType
TWITTER: AppType
WEB_BROWSER: AppType
RESPONSE_UNKNOWN: ResponseCode
SUCCESS: ResponseCode
FAILED: ResponseCode
MESSAGE: ResponseCode
ACTION_REQUIRED: ResponseCode
FINISHED: ResponseCode
UNKNOWN_ACTION: ActionType
INFORMATION: ActionType
SINGLE_SELECTION: ActionType
MULTIPLE_SELECTION: ActionType
CONFIRMATION: ActionType

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

class AppSchemaRequest(_message.Message):
    __slots__ = ("type",)
    TYPE_FIELD_NUMBER: _ClassVar[int]
    type: AppType
    def __init__(self, type: _Optional[_Union[AppType, str]] = ...) -> None: ...

class AppSchemaResponse(_message.Message):
    __slots__ = ("schema", "description")
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    schema: str
    description: str
    def __init__(self, schema: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class ChatRequest(_message.Message):
    __slots__ = ("type", "instruction")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    INSTRUCTION_FIELD_NUMBER: _ClassVar[int]
    type: AppType
    instruction: str
    def __init__(self, type: _Optional[_Union[AppType, str]] = ..., instruction: _Optional[str] = ...) -> None: ...

class ActionResultRequest(_message.Message):
    __slots__ = ("action_id", "action_result")
    ACTION_ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_RESULT_FIELD_NUMBER: _ClassVar[int]
    action_id: str
    action_result: str
    def __init__(self, action_id: _Optional[str] = ..., action_result: _Optional[str] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ("code", "request_id", "thread_id", "chat_response", "action_response", "empty")
    CODE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    THREAD_ID_FIELD_NUMBER: _ClassVar[int]
    CHAT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ACTION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    EMPTY_FIELD_NUMBER: _ClassVar[int]
    code: ResponseCode
    request_id: str
    thread_id: str
    chat_response: ChatResponse
    action_response: ActionRequiredResponse
    empty: _empty_pb2.Empty
    def __init__(self, code: _Optional[_Union[ResponseCode, str]] = ..., request_id: _Optional[str] = ..., thread_id: _Optional[str] = ..., chat_response: _Optional[_Union[ChatResponse, _Mapping]] = ..., action_response: _Optional[_Union[ActionRequiredResponse, _Mapping]] = ..., empty: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ...) -> None: ...

class ChatResponse(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class ActionRequiredResponse(_message.Message):
    __slots__ = ("type", "action_id", "message", "options")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ACTION_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    type: ActionType
    action_id: str
    message: str
    options: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, type: _Optional[_Union[ActionType, str]] = ..., action_id: _Optional[str] = ..., message: _Optional[str] = ..., options: _Optional[_Iterable[str]] = ...) -> None: ...
