from typing import Dict, Any, Type, cast

from pydantic import BaseModel
import openai


def sanitize_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    schema = openai.pydantic_function_tool(model)

    # remove unnecessary title
    schema.pop("title", None)

    properties = cast(dict, schema["function"]["parameters"].get("properties", {}))

    for prop in properties.values():
        prop.pop("title", None)
        # remove default values since it's not supported in structured output
        prop.pop("default", None)

    # remove empty properties
    if len(properties) == 0:
        schema.pop("properties", None)

    return schema["function"]["parameters"]
