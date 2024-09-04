from typing import Dict, Any, Type, cast

from pydantic import BaseModel
import openai


def sanitize_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    schema = openai.pydantic_function_tool(model)

    # remove unnecessary title
    schema.pop("title", None)

    parameters = schema["function"]["parameters"]
    properties = cast(dict, parameters.get("properties", {}))
    defs = cast(dict, parameters.get("$defs", {}))
    all_of = cast(list, parameters.get("allOf", []))

    # if allOf is present and properties is empty, it's likely a reference to another model
    # so we need to copy the properties from the referenced model
    if not properties and len(all_of) == 1:
        model_name = all_of[0]["$ref"].split("/")[-1]
        model_fields = defs[model_name]
        # copy properties from the referenced model
        for field, value in model_fields.items():
            parameters[field] = value
        parameters.pop("allOf", None)
        properties = cast(dict, parameters.get("properties", {}))

    for prop in properties.values():
        prop.pop("title", None)
        # remove default values since it's not supported in structured output
        prop.pop("default", None)

    # remove empty properties
    if len(properties) == 0:
        schema.pop("properties", None)

    return schema["function"]["parameters"]
