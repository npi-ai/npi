from pydantic import Field
from npi.types import Parameters


class MessageParameters(Parameters):
    to: str = Field(default=None, description='the phone number you want to send the message to')
    message: str = Field(default=100, description='the message body you want to send')

