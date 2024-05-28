from typing import TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from npi.core.thread import Thread, ThreadMessage


class Parameters(BaseModel):
    """Base parameter model for tool definitions"""

    npi_watch: int = Field(
        default=0,
        description="""
        Interval (in seconds) for detecting changes in the return value of this tool.
        If set to 0, the tool will not detect changes and will immediately returns.
        If set to a positive integer, the tool will not return anything until a change in the return value is detected.
        This is useful when you need to listen to the changes. For example, if you want to check new
        emails in the inbox, you may call `get_emails({ "query": "is:unread", "npi_watch": 3 })`
        and it will call the tool every 3 seconds and if a new email arrives, it will return the following diff:
        { "previous": Email[], "current": Email[] }
        """
    )

    _thread: 'Thread'
    _message: 'ThreadMessage'

    def __init__(self, _thread: 'Thread', _message: 'ThreadMessage', **args):
        super().__init__(**args)
        self._thread = _thread
        self._message = _message

    @classmethod
    def get_meta_schema(cls):
        schema = cls.model_json_schema()
        schema['properties'].pop('npi_watch')
        return schema

    def get_thread(self) -> 'Thread':
        return self._thread

    def get_message(self) -> 'ThreadMessage':
        return self._message

    # remove "title" property from pydantic json schema
    @classmethod
    def __get_pydantic_json_schema__(cls, __core_schema, __handler):
        schema = super().__get_pydantic_json_schema__(__core_schema, __handler)

        schema.pop('title', None)
        for prop in schema.get('properties', {}).values():
            prop.pop('title', None)

            # use a more compact format for optional fields
            if 'anyOf' in prop and len(prop['anyOf']) == 2 and prop['anyOf'][1]['type'] == 'null':
                # copy the first type definition to props
                t = prop['anyOf'][0]
                for k, v in t.items():
                    prop[k] = v

                prop.pop('anyOf', None)

                if prop.get('default') is None:
                    prop.pop('default', None)

        # remove empty properties
        if len(schema.get('properties', {})) == 0:
            schema.pop('properties', None)

        return schema
