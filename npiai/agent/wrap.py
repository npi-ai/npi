from typing import overload
from npiai import FunctionTool, BrowserTool, AgentTool, BrowserAgentTool, LLM


@overload
def wrap(tool: FunctionTool, llm: LLM = None) -> AgentTool: ...


@overload
def wrap(tool: BrowserTool, llm: LLM = None) -> BrowserAgentTool: ...


def wrap(
    tool: FunctionTool | BrowserTool, llm: LLM = None
) -> AgentTool | BrowserAgentTool:
    if isinstance(tool, BrowserTool):
        return BrowserAgentTool(tool, llm)

    if isinstance(tool, FunctionTool):
        return AgentTool(tool, llm)

    raise TypeError(f"app must be an instance of FunctionTool or BrowserTool")
