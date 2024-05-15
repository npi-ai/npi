from npiai.core.base import App
from npiai.core.hitl import HITLHandler
from openai import Client
from openai.types.chat import ChatCompletionMessageToolCallParam, ChatCompletionFunctionMessageParam

from npiai.tools.hitl import EmptyHandler
import json



class ToolSet:

    @staticmethod
    def builder() -> 'ToolSet':
        return ToolSet()

    def __init__(self):
        self._tools: dict[str, App] = {}
        self._hitl_handler = None
        self._fixed = False
        self._llm = None

    def llm(self, llm: Client) -> 'ToolSet':
        if self._fixed:
            raise Exception("ToolSet is immutable.")
        self._llm = llm
        return self

    def hitl(self, handler: HITLHandler) -> 'ToolSet':
        if self._fixed:
            raise Exception("ToolSet is immutable.")
        self._hitl_handler = handler
        return self

    def use(self, *tools: App) -> 'ToolSet':
        if self._fixed:
            raise Exception("ToolSet is immutable.")
        for tool in tools:
            self._tools[tool.tool_name()] = tool
        return self

    def build(self) -> 'ToolSet':
        if self._llm is None:
            raise Exception("Client is required.")

        if len(self._tools) == 0:
            raise Exception("At least one tool is required.")

        if self._hitl_handler is None:
            self._hitl_handler = EmptyHandler()

        self._fixed = True
        return self

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
