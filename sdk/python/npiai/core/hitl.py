from abc import ABC, abstractmethod
from enum import Enum

from npiai_proto import api_pb2


class ActionRequestCode(Enum):
    UNKNOWN_ACTION = 0
    INFORMATION = 1
    SINGLE_SELECTION = 2
    MULTIPLE_SELECTION = 3
    CONFIRMATION = 4


class ActionResultCode(Enum):
    APPROVED = 0
    DENIED = 1
    MESSAGE = 2
    SUCCESS = 3


class HITLRequest:
    def __init__(self, code: ActionRequestCode, message: str, app_name: str = 'Unknown'):
        self.code = code
        self.app_name = app_name
        self.message = message


class HITLResponse:
    def __init__(self, code: ActionResultCode, msg: str = None):
        self.code = code
        self.message = msg


ACTION_APPROVED = HITLResponse(ActionResultCode.APPROVED)
ACTION_DENIED = HITLResponse(ActionResultCode.DENIED)


class HITLHandler(ABC):
    @abstractmethod
    def handle(self, req: HITLRequest) -> HITLResponse:
        pass

    @abstractmethod
    def type(self) -> api_pb2.ActionType:
        pass


def convert_to_hitl_request(req: api_pb2.ActionRequiredResponse, app_name: str = None) -> HITLRequest:
    match req.type:
        case api_pb2.ActionType.INFORMATION:
            return HITLRequest(
                code=ActionRequestCode.INFORMATION,
                message=req.message,
                app_name=app_name,
            )
        case api_pb2.ActionType.CONFIRMATION:
            return HITLRequest(
                code=ActionRequestCode.CONFIRMATION,
                message=req.message,
                app_name=app_name,
            )
        case api_pb2.ActionType.SINGLE_SELECTION:
            return HITLRequest(
                code=ActionRequestCode.SINGLE_SELECTION,
                message=req.message,
                app_name=app_name,
            )
        case api_pb2.ActionType.MULTIPLE_SELECTION:
            return HITLRequest(
                code=ActionRequestCode.MULTIPLE_SELECTION,
                message=req.message,
                app_name=app_name,
            )
    return HITLRequest(
        code=ActionRequestCode.UNKNOWN_ACTION,
        message="invalid action request",
        app_name=app_name,
    )
