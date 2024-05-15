from npiai.core.hitl import (
    HITLHandler, HITLRequest, HITLResponse, ActionRequestCode, ActionResultCode, ACTION_APPROVED, ACTION_DENIED)

from npiai_proto import api_pb2


class EmptyHandler(HITLHandler):
    def handle(self, req: HITLRequest) -> HITLResponse:
        match req.code:
            case ActionRequestCode.INFORMATION:
                return HITLResponse(
                    code=ActionResultCode.SUCCESS,
                    msg="No human can response your help",
                )
            case ActionRequestCode.CONFIRMATION:
                return HITLResponse(
                    code=ActionResultCode.APPROVED,
                    msg="automatically approved",
                )
        return ACTION_DENIED

    def type(self) -> api_pb2.ActionType:
        return api_pb2.ActionType.CONSOLE
