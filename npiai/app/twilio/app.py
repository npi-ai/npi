import os

from twilio.rest import Client

from npiai import App, function
from npiai.error.auth import UnauthorizedError


class Twilio(App):
    def __init__(self, account_sid: str = None, auth_token: str = None, from_number: str = None):
        super().__init__(
            name='twilio',
            description='Send messages using Twilio, e.g., twilio("send a message to +16507055795")',
            system_prompt='You are a Twilio Agent can send messages via WhatsApp or SMS',
        )

        sid = account_sid or os.environ.get('TWILIO_ACCOUNT_SID', None)
        token = auth_token or os.environ.get('TWILIO_AUTH_TOKEN', None)

        if not sid:
            raise UnauthorizedError('Twilio account sid is missing')
        if not token:
            raise UnauthorizedError('Twilio auth token is missing')

        self.client = Client(sid, token)
        self.from_number = from_number or os.environ.get('TWILIO_FROM_NUMBER', None)

    @function
    async def send_sms_message(self, to: str, body: str) -> str:
        """
        Send a sms message to a phone number.

        Args:
            to: The phone number you want to send the message to.
            body: The body of the message.
        """
        message = self.client.messages.create(
            from_=f'{self.from_number}',
            body=body,
            to=to,
        )

        return f'Message has been successfully sent, sid: {message.sid}'

    @function
    async def send_whatsapp_message(self, to: str, body: str) -> str:
        """
        Send a whatsapp message to a phone number.

        Args:
            to: The phone number you want to send the message to.
            body: The body of the message.
        """
        message = self.client.messages.create(
            from_=f'whatsapp:{self.from_number}',
            body=body,
            to=f'whatsapp:{to}',
        )

        return f'Message has been successfully sent, sid: {message.sid}'
