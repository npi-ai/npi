from typing import overload
from npiai import FunctionTool, BrowserTool, AgentTool, BrowserAgentTool, LLM


@overload
def wrap(tool: FunctionTool) -> AgentTool: ...


@overload
def wrap(tool: BrowserTool) -> BrowserAgentTool: ...


def wrap(tool: FunctionTool | BrowserTool) -> AgentTool | BrowserAgentTool:
    if isinstance(tool, BrowserTool):
        return BrowserAgentTool(tool)

    if isinstance(tool, FunctionTool):
        return AgentTool(tool)

    raise TypeError(f"app must be an instance of FunctionTool or BrowserTool")
