"""the basic interface for the natural language programming interface"""
from abc import ABC, abstractmethod
import json

from openai import Client


class App(ABC):
    """the basic interface for the natural language programming interface"""

    llm: Client
    default_model: str
    tool_choice: str
    functions = {}

    def __init__(self, llm, mode="gpt-4-turbo-preview", tool_choice="auto"):
        self.llm = llm
        self.default_model = mode
        self.tool_choice = tool_choice

    def _register_functions(self, functions):
        self.functions = functions

    @abstractmethod
    def chat(self, message, context=None) -> str:
        """the chat function for the app"""

    def _call_llm(self, messages, functions):
        tools = []
        for func in functions.copy().values():
            tools.append({"type": "function", "function": func})

        response = self.llm.chat.completions.create(
            model=self.default_model,
            messages=messages,
            tools=tools,
            tool_choice=self.tool_choice,
        )
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        if tool_calls:
            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = self.functions[function_name]
                function_response = function_to_call(
                    json.loads(tool_call.function.arguments))
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
            second_response = self.llm.chat.completions.create(
                model=self.default_model,
                messages=messages,
            )  # get a new response from the model where it can see the function response
            return second_response
        else:
            return response_message
