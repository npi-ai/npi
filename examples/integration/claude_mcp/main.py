import asyncio
import os

from mcp.server.stdio import stdio_server

from npiai import Context
from npiai.llm import Anthropic
from npiai.integration.mcp import create_mcp_server

# from npiai.tools.web.chromium import Chromium
from npiai.tools import GitHub


async def main():
    # async with Chromium(headless=False) as tool:
    async with GitHub() as tool:
        ctx = Context()
        ctx.use_llm(
            Anthropic(
                model="claude-3.5",
                api_key=os.environ.get("ANTHROPIC_API_KEY"),
            )
        )
        server = await create_mcp_server(ctx, tool)
        options = server.create_initialization_options()

        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                options,
                raise_exceptions=True,
            )


if __name__ == "__main__":
    asyncio.run(main())
