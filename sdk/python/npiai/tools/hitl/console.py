from termcolor import colored
from npiai.core.hitl import (
    HITLHandler, HITLRequest, HITLResponse, ActionRequestCode, ActionResultCode, ACTION_APPROVED, ACTION_DENIED)

from npiai_proto import api_pb2


class ConsoleHandler(HITLHandler):
    def handle(self, req: HITLRequest) -> HITLResponse:
        match req.code:
            case ActionRequestCode.INFORMATION:
                print(colored(f"[{req.app_name}]: Additional information Required", 'green', attrs=['bold']))
                print(colored(f"[{req.app_name}]: Agent Request: ", 'green', attrs=['bold']))
                human_response = input(colored(f'[{req.app_name}]: Type Your Response: ', 'magenta'))
                return HITLResponse(
                    code=ActionResultCode.SUCCESS,
                    msg=human_response,
                )
            case ActionRequestCode.CONFIRMATION:
                print(colored(f"[{req.app_name}]: Action request for approving", 'green', attrs=['bold']))
                print(colored(f"[{req.app_name}]: Action Detail:\n\n{req.message}", 'green', attrs=['bold']))
                human_response = input(colored(f'[{req.app_name}]: [Yes/No?] > ', 'magenta'))
                if human_response.lower() == "yes":
                    resp = ACTION_APPROVED
                else:
                    resp = ACTION_DENIED
                human_response = input(colored(f'[{req.app_name}]: Do you want give a message back? (typing Enter to '
                                               f'skip) > ', 'magenta'))
                if human_response is not None:
                    resp.message = human_response
                return resp
        return ACTION_DENIED

    def type(self) -> api_pb2.ActionType:
        return api_pb2.ActionType.CONSOLE
