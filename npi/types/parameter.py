from pydantic import BaseModel
from openai.types.chat import ChatCompletionMessageParam
from typing import List


class Parameter(BaseModel):
    """
        Base parameter model for tool definitions

        Attributes:
              _messages: llm messages so far
    """
    _messages: List[ChatCompletionMessageParam]

    def __init__(self, _messages: List[ChatCompletionMessageParam], **args):
        super().__init__(**args)
        self._prompt = _messages

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
