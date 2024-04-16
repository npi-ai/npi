from pydantic import BaseModel
from openai.types.chat import ChatCompletionMessageParam
from typing import List

from npi.core.thread import Thread, ThreadMessage


class Parameters(BaseModel):
    """Base parameter model for tool definitions"""

    _thread: Thread
    _message: ThreadMessage

    def __init__(self, _thread: Thread, _message: ThreadMessage, **args):
        super().__init__(**args)
        self._thread = _thread
        self._message = _message

    def get_thread(self) -> Thread:
        return self._thread

    def get_message(self) -> ThreadMessage:
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


if __name__ == '__main__':
    p = Parameters(_thread={}, _message={})
    print(p)
