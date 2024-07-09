from npiai.core import BaseTool
from .toolkit import NPiLangChainToolkit


def create_tool(tool: BaseTool) -> NPiLangChainToolkit:
    return NPiLangChainToolkit(tool)
