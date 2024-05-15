from npiai.core.base import App
from npiai.core.hitl import HITLHandler
from openai import Client

from npiai.tools.hitl import EmptyHandler
import json
from typing import List


class ToolSet:

    def __init__(self, tools: List[App], llm: Client, hitl_handler: HITLHandler = None, ):
        if len(tools) == 0:
            raise Exception("At least one tool is required.")
        self._tools = {}
        for tool in tools:
            tool.authorize()
            self._tools[tool.tool_name()] = tool
        self._llm = llm

        self._hitl_handler = hitl_handler
        if self._hitl_handler is None:
            self._hitl_handler = EmptyHandler()

    def openai(self):
        tools = []
        for tool in self._tools.values():
            tools.append(tool.schema())
        return tools

    def call(self, body) -> str:
        tool = self._tools.get(body.function.name)
        if tool is None:
            return "Tool not found"
        params = json.loads(body.function.arguments)

        return tool.chat(params['message'])
