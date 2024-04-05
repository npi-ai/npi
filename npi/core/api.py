"""the basic interface for the natural language programming interface"""
from abc import ABC, abstractmethod
import json
import logging
from typing import Dict, List, Tuple, Literal, Optional, overload

from pydantic import Field
from openai import Client
from openai.types.chat import (
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    ChatCompletionMessageParam,
)

from npi.types import FunctionRegistration, Parameter

logger = logging.getLogger()


class ChatParameter(Parameter):
    task: str = Field(description='The task you want {{app_name}} to do')


class App(ABC):
    """the basic interface for the natural language programming interface"""

    llm: Client
    default_model: str
    tool_choice: ChatCompletionToolChoiceOptionParam
    tools: List[ChatCompletionToolParam]
    fn_map: Dict[str, FunctionRegistration]
    name: str
    description: str
    system_role: Optional[str]

    def __init__(
        self,
        name: str,
        description: str,
        llm: Client = None,
        system_role: str = None,
        model: str = "gpt-4-turbo-preview",
        tool_choice: ChatCompletionToolChoiceOptionParam = "auto"
    ):
        self.name = name
        self.description = description
        self.llm = llm
        self.default_model = model
        self.tool_choice = tool_choice
        self.system_role = system_role
        self.fn_map = {}
        self.tools = []

        for fn_reg in self.get_functions():
            self.register(fn_reg)

    @abstractmethod
    def get_functions(self) -> List[FunctionRegistration]:
        """Get the list of function registrations"""

    def register(
        self,
        fn_reg: FunctionRegistration,
    ):
        """
        Register a function used in tool calls

        Args:
            fn_reg: the function registration object
        """
        if fn_reg.name in self.fn_map:
            raise Exception(f'Duplicate function: {fn_reg.name}')

        self.fn_map[fn_reg.name] = fn_reg

        tool: ChatCompletionToolParam = {
            'type': 'function',
            'function': {
                'name': fn_reg.name,
                'description': fn_reg.description,
            }
        }

        if fn_reg.Params is not None:
            tool['function']['parameters'] = fn_reg.Params.model_json_schema()

        self.tools.append(tool)

    @overload
    def chat(
        self,
        message: str | ChatParameter,
        context: List[ChatCompletionMessageParam] = None,
        return_history: Literal[False] = False,
    ) -> str:
        ...

    @overload
    def chat(
        self,
        message: str | ChatParameter,
        context: List[ChatCompletionMessageParam] = None,
        return_history: Literal[True] = True,
    ) -> Tuple[str, List[ChatCompletionMessageParam]]:
        ...

    def chat(
        self,
        message: str | ChatParameter,
        context: List[ChatCompletionMessageParam] = None,
        return_history: bool = False,
    ) -> str | Tuple[str, List[ChatCompletionMessageParam]]:
        """
        The chat function for the app

        Args:
            message: the message passing to the llm
            context: chat history context
            return_history: whether to return the history of the llm call

        Returns:
            The last chat message if return_history is False, otherwise a tuple of (last message, chat history)
        """
        prompts: List[ChatCompletionMessageParam] = []

        if self.system_role:
            prompts.append(
                {
                    'role': 'system',
                    'content': self.system_role
                }
            )

        if context:
            for msg in context:
                if msg.get('role') != 'system':
                    prompts.append(msg)

        user_prompt: str = message.task if isinstance(message, ChatParameter) else message

        prompts.append(
            {
                'role': 'user',
                'content': user_prompt
            }
        )

        response, history = self._call_llm(prompts)

        if return_history:
            return response, history

        return response

    def as_tool(self) -> FunctionRegistration:
        """
        Wrap the chat function of this app to FunctionRegistration

        Returns:
            FunctionRegistration
        """

        class AppChatParameter(ChatParameter):
            task: str = Field(description=f'The task you want {self.name} to do')

        return FunctionRegistration(
            fn=self.chat,
            name=self.name,
            Params=AppChatParameter,
            description=self.description,
        )

    def _call_llm(self, prompts: List[ChatCompletionMessageParam]) -> Tuple[str, List[ChatCompletionMessageParam]]:
        """
        Call llm with the given prompts

        Args:
            prompts: llm prompts

        Returns:
            (last message, chat history)
        """
        history = prompts.copy()

        while True:
            response = self.llm.chat.completions.create(
                model=self.default_model,
                messages=history,
                tools=self.tools,
                tool_choice=self.tool_choice,
            )

            response_message = response.choices[0].message
            # noinspection PyTypeChecker
            # type `ChatCompletionMessage` is allowed here
            history.append(
                response_message.dict(exclude_unset=True)
            )

            if response_message.content:
                print(response_message.content + '\n')

            tool_calls = response_message.tool_calls

            if tool_calls is None:
                break

            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                fn_reg = self.fn_map[fn_name]
                args = json.loads(tool_call.function.arguments)
                print(f'Calling {fn_name}({args})\n')
                if fn_reg.Params is not None:
                    res = fn_reg.fn(fn_reg.Params(_messages=history, **args))
                else:
                    res = fn_reg.fn()
                # print(res)
                history.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fn_name,
                        "content": res,
                    }
                )

        return response_message.content, history
