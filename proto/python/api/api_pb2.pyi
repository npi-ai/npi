from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import wrappers_pb2 as _wrappers_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AppType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    APP_UNKNOWN: _ClassVar[AppType]
    GOOGLE_GMAIL: _ClassVar[AppType]
    GOOGLE_CALENDAR: _ClassVar[AppType]
    GITHUB: _ClassVar[AppType]
    SLACK: _ClassVar[AppType]
    DISCORD: _ClassVar[AppType]
    TWITTER: _ClassVar[AppType]

class ChatResponseType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    APP_UNSUPPORTED: _ClassVar[ChatResponseType]
    SUCCESS: _ClassVar[ChatResponseType]
    FAILED: _ClassVar[ChatResponseType]
    MESSAGE: _ClassVar[ChatResponseType]
    HUMAN_FEEDBACK: _ClassVar[ChatResponseType]
    SAFEGUARD: _ClassVar[ChatResponseType]
APP_UNKNOWN: AppType
GOOGLE_GMAIL: AppType
GOOGLE_CALENDAR: AppType
GITHUB: AppType
SLACK: AppType
DISCORD: AppType
TWITTER: AppType
APP_UNSUPPORTED: ChatResponseType
SUCCESS: ChatResponseType
FAILED: ChatResponseType
MESSAGE: ChatResponseType
HUMAN_FEEDBACK: ChatResponseType
SAFEGUARD: ChatResponseType

class ChatRequest(_message.Message):
    __slots__ = ("request_id", "app_type", "instruction", "thread_id")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    APP_TYPE_FIELD_NUMBER: _ClassVar[int]
    INSTRUCTION_FIELD_NUMBER: _ClassVar[int]
    THREAD_ID_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    app_type: AppType
    instruction: str
    thread_id: str
    def __init__(self, request_id: _Optional[str] = ..., app_type: _Optional[_Union[AppType, str]] = ..., instruction: _Optional[str] = ..., thread_id: _Optional[str] = ...) -> None: ...

class ChatResponse(_message.Message):
    __slots__ = ("request_id", "type", "message")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    type: ChatResponseType
    message: str
    def __init__(self, request_id: _Optional[str] = ..., type: _Optional[_Union[ChatResponseType, str]] = ..., message: _Optional[str] = ...) -> None: ...
