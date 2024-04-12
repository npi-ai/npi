from pydantic import Field
from npi.types import Parameters


class GotoParameters(Parameters):
    url: str = Field(description='The url to go to')
