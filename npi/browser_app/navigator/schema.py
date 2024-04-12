from pydantic import Field
from npi.types import Parameters


class BaseActionParameters(Parameters):
    id: str = Field(description='Target element id')
    description: str = Field(
        description='A brief description for this operation. For example, "Type \'the answer to everything\' into the search box"'
    )


class ClickParameters(BaseActionParameters):
    pass


class FillParameters(BaseActionParameters):
    value: str = Field('Text to fill in the element')


class SelectParameters(BaseActionParameters):
    value: str = Field('Option value to select')


class EnterParameters(BaseActionParameters):
    pass
