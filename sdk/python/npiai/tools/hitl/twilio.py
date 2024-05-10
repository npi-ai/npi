import datetime
import time

from twilio.rest import Client
import loguru

from npiai.core.hitl import (
    HITLHandler, HITLRequest, HITLResponse, ActionRequestCode, ACTION_APPROVED, ACTION_DENIED)

from npiai_proto import api_pb2


class TwilioHandler(HITLHandler):
    def __init__(self, account_id: str, auth_token: str,
                 from_number: str, to_number: str, sms: bool = True):
        self.account_id = account_id
        self.auth_token = auth_token
        self.from_phone_number = from_number
        self.client = Client(account_id, auth_token)
        self.to_number = to_number
        self.sms = sms

    def handle(self, req: HITLRequest) -> HITLResponse:
        match req.code:
            case ActionRequestCode.INFORMATION:
                notice = f'[{req.app_name}]: Additional information Required\n'
                notice += f'[{req.app_name}]: Agent Request: '
                notice += f'{req.message}'
            case ActionRequestCode.CONFIRMATION:
                notice = f'[{req.app_name}]: Action request for approving\n'
                notice += f'[{req.app_name}]: Action Detail:\n\n{req.message} '
                notice += f'[{req.app_name}]: [Yes/No?]'
            case _:
                return ACTION_DENIED

        message = self.client.messages.create(
            from_=self.from_phone_number,
            body=notice,
            to=self.to_number,
        )
        print(f'Message has been successfully sent, sid: {message.sid}')
        human_response = self.__wait_reply(datetime.datetime.utcnow())
        if human_response.lower() == "yes":
            resp = ACTION_APPROVED
        else:
            resp = ACTION_DENIED
        return resp

    def type(self) -> api_pb2.ActionType:
        return api_pb2.ActionType.CONSOLE

    def __wait_reply(self, after: datetime) -> str:
        print('Waiting for a reply...')
        while True:
            msgs = self.client.messages.list(from_=self.to_number, date_sent_after=after)
            if len(msgs) > 0:
                loguru.logger.info(f'received reply from: {msgs[0].from_}, body: {msgs[0].body}')
                return msgs[0].body
            time.sleep(1)
