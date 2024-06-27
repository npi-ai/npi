from twilio.rest import Client

from npi.core.app import App, npi_tool
from npi.config import config

from npi.app.twilio.schema import *


class Twilio(App):
    def __init__(self):
        super().__init__(
            name='twilio',
            description='Send messages using Twilio, e.g., twilio("send a message to +16507055795")',
            system_role='You are a Twilio Agent can send messages via WhatsApp or SMS',
        )

        cred = config.get_twilio_credentials()
        self.client = Client(cred.account_sid, cred.auth_token)
        self.from_number = cred.from_phone_number

    @npi_tool(description='Send a sms message to a phone number')
    async def send_sms_message(self, params: MessageParameters):
        message = self.client.messages.create(
            from_=f'{self.from_number}',
            body=params.message,
            to=f"{params.to}",
        )

        return f'Message has been successfully sent, sid: {message.sid}'

    @npi_tool(description='Send a whatsapp message to a phone number')
    async def send_whatsapp_message(self, params: MessageParameters):
        message = self.client.messages.create(
            from_=f'whatsapp:{self.from_number}',
            body=params.message,
            to=f"whatsapp:{params.to}",
        )

        return f'Message has been successfully sent, sid: {message.sid}'
