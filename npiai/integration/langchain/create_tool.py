from npiai.core import BaseTool
from npiai.context import Context
from .toolkit import NPiLangChainToolkit


def create_tool(ctx: Context, tool: BaseTool) -> NPiLangChainToolkit:
    return NPiLangChainToolkit(ctx, tool)
