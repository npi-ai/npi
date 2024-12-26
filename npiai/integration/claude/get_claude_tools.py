from npiai.core import BaseTool
from npiai.utils import sanitize_schema

__EMPTY_INPUT_SCHEMA__ = {"type": "object", "properties": {}, "required": []}


def get_claude_tools(tool: BaseTool):
    tools = []

    for fn_reg in tool.unpack_functions():
        tool = {
            "name": fn_reg.name,
            "description": fn_reg.description,
            "input_schema": (
                sanitize_schema(fn_reg.model, strict=False)
                if fn_reg.model
                else __EMPTY_INPUT_SCHEMA__
            ),
        }

        tools.append(tool)

    return tools
