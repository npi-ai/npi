from typing import Dict, Any, Type

from pydantic import BaseModel


def sanitize_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    schema = model.model_json_schema()

    # remove unnecessary title
    schema.pop("title", None)

    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)

        # use a more compact format for optional fields
        if (
            "anyOf" in prop
            and len(prop["anyOf"]) == 2
            and prop["anyOf"][1]["type"] == "null"
        ):
            # copy the first type definition to props
            t = prop["anyOf"][0]
            for k, v in t.items():
                prop[k] = v

            prop.pop("anyOf", None)

            if prop.get("default") is None:
                prop.pop("default", None)

    # remove empty properties
    if len(schema.get("properties", {})) == 0:
        schema.pop("properties", None)

    return schema
