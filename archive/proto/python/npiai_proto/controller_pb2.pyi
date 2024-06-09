from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Language(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_LANGUAGE: _ClassVar[Language]
    PYTHON: _ClassVar[Language]
    NODEJS: _ClassVar[Language]

class ParameterType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_TYPE: _ClassVar[ParameterType]
    STRING: _ClassVar[ParameterType]
    INT: _ClassVar[ParameterType]
    FLOAT: _ClassVar[ParameterType]
    BOOL: _ClassVar[ParameterType]
    MAP: _ClassVar[ParameterType]
    LIST: _ClassVar[ParameterType]
    FILE: _ClassVar[ParameterType]
    IMAGE: _ClassVar[ParameterType]
    AUDIO: _ClassVar[ParameterType]
    VIDEO: _ClassVar[ParameterType]
    DATETIME: _ClassVar[ParameterType]
    EMAIL: _ClassVar[ParameterType]
UNKNOWN_LANGUAGE: Language
PYTHON: Language
NODEJS: Language
UNKNOWN_TYPE: ParameterType
STRING: ParameterType
INT: ParameterType
FLOAT: ParameterType
BOOL: ParameterType
MAP: ParameterType
LIST: ParameterType
FILE: ParameterType
IMAGE: ParameterType
AUDIO: ParameterType
VIDEO: ParameterType
DATETIME: ParameterType
EMAIL: ParameterType

class RegisterToolRequest(_message.Message):
    __slots__ = ("tool", "hostname", "ip", "port")
    TOOL_FIELD_NUMBER: _ClassVar[int]
    HOSTNAME_FIELD_NUMBER: _ClassVar[int]
    IP_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    tool: ToolSpec
    hostname: str
    ip: str
    port: int
    def __init__(self, tool: _Optional[_Union[ToolSpec, _Mapping]] = ..., hostname: _Optional[str] = ..., ip: _Optional[str] = ..., port: _Optional[int] = ...) -> None: ...

class RegisterToolResponse(_message.Message):
    __slots__ = ("token",)
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    token: str
    def __init__(self, token: _Optional[str] = ...) -> None: ...

class UnregisterToolRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class HeartbeatRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ToolSpec(_message.Message):
    __slots__ = ("metadata", "function_spec")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_SPEC_FIELD_NUMBER: _ClassVar[int]
    metadata: Metadata
    function_spec: FunctionSpec
    def __init__(self, metadata: _Optional[_Union[Metadata, _Mapping]] = ..., function_spec: _Optional[_Union[FunctionSpec, _Mapping]] = ...) -> None: ...

class Metadata(_message.Message):
    __slots__ = ("id", "name", "version", "description", "author", "agent_mode")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    AGENT_MODE_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    version: str
    description: str
    author: str
    agent_mode: bool
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., version: _Optional[str] = ..., description: _Optional[str] = ..., author: _Optional[str] = ..., agent_mode: bool = ...) -> None: ...

class FunctionSpec(_message.Message):
    __slots__ = ("runtime", "dependencies", "functions")
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    DEPENDENCIES_FIELD_NUMBER: _ClassVar[int]
    FUNCTIONS_FIELD_NUMBER: _ClassVar[int]
    runtime: Runtime
    dependencies: _containers.RepeatedCompositeFieldContainer[Dependency]
    functions: _containers.RepeatedCompositeFieldContainer[Function]
    def __init__(self, runtime: _Optional[_Union[Runtime, _Mapping]] = ..., dependencies: _Optional[_Iterable[_Union[Dependency, _Mapping]]] = ..., functions: _Optional[_Iterable[_Union[Function, _Mapping]]] = ...) -> None: ...

class Runtime(_message.Message):
    __slots__ = ("language", "version", "image")
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    language: Language
    version: str
    image: str
    def __init__(self, language: _Optional[_Union[Language, str]] = ..., version: _Optional[str] = ..., image: _Optional[str] = ...) -> None: ...

class Dependency(_message.Message):
    __slots__ = ("name", "version")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    name: str
    version: str
    def __init__(self, name: _Optional[str] = ..., version: _Optional[str] = ...) -> None: ...

class Function(_message.Message):
    __slots__ = ("name", "description", "parameters", "few_shots")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    FEW_SHOTS_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    parameters: _containers.RepeatedCompositeFieldContainer[Parameter]
    few_shots: _containers.RepeatedCompositeFieldContainer[FewShot]
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ..., parameters: _Optional[_Iterable[_Union[Parameter, _Mapping]]] = ..., few_shots: _Optional[_Iterable[_Union[FewShot, _Mapping]]] = ...) -> None: ...

class Parameter(_message.Message):
    __slots__ = ("name", "description", "type", "default", "required")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    type: str
    default: str
    required: bool
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ..., type: _Optional[str] = ..., default: _Optional[str] = ..., required: bool = ...) -> None: ...

class FewShot(_message.Message):
    __slots__ = ("input", "output")
    INPUT_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    input: str
    output: str
    def __init__(self, input: _Optional[str] = ..., output: _Optional[str] = ...) -> None: ...
