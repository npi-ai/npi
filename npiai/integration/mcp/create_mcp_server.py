from typing import Any, Dict

from mcp.server import Server
from mcp.types import (
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
)

from npiai.core import BaseTool
from npiai.context import Context
from npiai.utils import sanitize_schema

__EMPTY_INPUT_SCHEMA__ = {"type": "object", "properties": {}, "required": []}


async def create_mcp_server(ctx: Context, tool: BaseTool) -> Server:
    server = Server(f"mcp_{tool.name}")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        res: list[Tool] = []

        for fn in tool.unpack_functions():
            res.append(
                Tool(
                    name=fn.name,
                    description=fn.description,
                    inputSchema=(
                        sanitize_schema(fn.model, strict=False)
                        if fn.model
                        else __EMPTY_INPUT_SCHEMA__
                    ),
                )
            )

        return res

    @server.call_tool()
    async def call_tool(name: str, args: Dict[str, Any]) -> list[TextContent]:
        res = await tool.exec(ctx, name, args)

        return [
            TextContent(
                type="text",
                text=res,
            )
        ]

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        res: list[Prompt] = []

        for fn in tool.unpack_functions():
            args: list[PromptArgument] = []

            for name, field in fn.model.model_fields.items():
                args.append(
                    PromptArgument(
                        name=name,
                        description=field.description,
                        required=field.is_required(),
                    )
                )

            res.append(
                Prompt(
                    name=fn.name,
                    description=fn.description,
                    arguments=args,
                )
            )

        return res

    @server.get_prompt()
    async def get_prompt(name: str, args: Dict[str, Any]) -> GetPromptResult:
        res = await tool.exec(ctx, name, args)

        return GetPromptResult(
            description=f"Execution result of {name}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=res,
                    ),
                )
            ],
        )

    return server
