from pydantic import BaseModel


class Parameter(BaseModel):
    # remove "title" property from pydantic json schema
    @classmethod
    def __get_pydantic_json_schema__(cls, __core_schema, __handler):
        schema = super().__get_pydantic_json_schema__(__core_schema, __handler)

        schema.pop('title', None)
        for prop in schema.get('properties', {}).values():
            prop.pop('title', None)

        return schema
