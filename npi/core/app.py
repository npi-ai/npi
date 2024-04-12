"""The basic interface for the natural language programming interface"""
import json
import logging
import inspect
import functools
from typing import Dict, List, Optional, Union, Type

from pydantic import Field
from openai import Client
from openai.types.chat import (
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from npi.types import FunctionRegistration, Parameters, ToolFunction
from npi.core.context import Thread, ThreadMessage
from npi.constants.openai import Role

logger = logging.getLogger()

__NPI_TOOL_ATTR__ = '__NPI_TOOL_ATTR__'


def npi_tool(
    tool_fn: ToolFunction = None,
    description: Optional[str] = None,
    Params: Optional[Type[Parameters]] = None
):
    """
    NPi Tool decorator for methods

    Args:
        tool_fn: Tool function. This value will be set automatically.
        description: Tool description. This value will be inferred from the tool's docstring if not given.
        Params: Tool parameters factory. This value will be inferred from the tool's type hints if not given.

    Returns:
        Wrapped tool function that will be registered on the app class
    """

    def decorator(fn: ToolFunction):
        setattr(fn, __NPI_TOOL_ATTR__, {'description': description, 'Params': Params})

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper

    # called as `@npi_tool`
    if callable(tool_fn):
        return decorator(tool_fn)

    # called as `@npi_tool(...)`
    return decorator


def _register_tools(app: 'App'):
    """
    Find the wrapped tool functions and register them in the app

    Args:
        app: NPi App instance
    """
    for attr in dir(app):
        fn = getattr(app, attr)
        tool_props = getattr(fn, __NPI_TOOL_ATTR__, None)

        if not callable(fn) or not tool_props:
            continue

        params = list(inspect.signature(fn).parameters.values())
        params_count = len(params)

        if params_count > 1:
            raise TypeError(
                f'Tool function `{fn.__name__}` should have at most 1 parameter, got {params_count}'
            )

        ParamsClass: Union[Type[Parameters], None] = None

        if params_count == 1:
            # this method is likely to receive a Parameter object
            ParamsClass = tool_props['Params'] or params[0].annotation

            if not ParamsClass or not issubclass(ParamsClass, Parameters):
                raise TypeError(
                    f'Tool function `{fn.__name__}`\'s parameter should have type {type(Parameters)}, got {type(ParamsClass)}'
                )

        description = tool_props['description'] or fn.__doc__

        if not description:
            raise ValueError(
                f'Unable to get the description of tool function `{fn.__name__}`'
            )

        app.register(
            FunctionRegistration(
                fn=fn,
                description=description,
                Params=ParamsClass
            )
        )


class ChatParameters(Parameters):
    task: str = Field(description='The task you want {{app_name}} to do')


class App:
    """The basic interface for the natural language programming interface"""

    instant_id: str
    tools: List[ChatCompletionToolParam]
    fn_map: Dict[str, FunctionRegistration]

    llm: Client
    default_model: str
    tool_choice: ChatCompletionToolChoiceOptionParam
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
        self.tools = []
        self.fn_map = {}
        _register_tools(self)

    def register(
        self,
        *tools: Union[FunctionRegistration, 'App'],
    ):
        """
        Register a tool to this application

        Args:
            *tools: the tools to register. If an app is provided, the `app.as_tool()` method will be called.
        """

        for tool in tools:
            fn_reg = tool.as_tool() if isinstance(tool, App) else tool

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

    def chat(
        self,
        message: str | ChatParameters,
        thread: Thread = None,
    ) -> str:
        """
        The chat function for the app

        Args:
            message: the message passing to the llm
            thread: the thread of this chat. A new thread will be created if not given

        Returns:
            The last chat message
        """

        user_prompt: str = message.task if isinstance(
            message, ChatParameters
        ) else message

        if thread is None:
            thread = Thread()

        msg = thread.fork(user_prompt)

        if self.system_role:
            msg.append(
                ChatCompletionSystemMessageParam(
                    content=self.system_role, role=Role.SYSTEM.value
                )
            )

        msg.append(
            ChatCompletionUserMessageParam(
                content=user_prompt, role=Role.USER.value
            )
        )
        response = self._call_llm(msg)
        msg.set_result(response)

        return response

    def as_tool(self) -> FunctionRegistration:
        """
        Wrap the chat function of this app to FunctionRegistration

        Returns:
            FunctionRegistration
        """

        class AppChatParameter(ChatParameters):  # pylint: disable=missing-class-docstring
            task: str = Field(
                description=f'The task you want {self.name} to do'
            )

        return FunctionRegistration(
            fn=self.chat,
            name=self.name,
            Params=AppChatParameter,
            description=self.description,
        )

    def on_round_end(self, context: ThreadMessage) -> None:
        """
        Callback function called at the end of a round
        Args:
            context: the thread message
        """
        pass

    def _call_llm(self, context: ThreadMessage) -> str:
        """
        Call llm with the given prompts

        Args:
            context: ThreadMessage context

        Returns:
            (last message, chat history)
        """
        while True:
            response = self.llm.chat.completions.create(
                model=self.default_model,
                messages=context.raw(),
                tools=self.tools,
                tool_choice=self.tool_choice,
                max_tokens=4096,
            )

            response_message = response.choices[0].message

            context.append(response_message)

            if response_message.content:
                print(response_message.content + '\n')

            tool_calls = response_message.tool_calls

            if tool_calls is None:
                self.on_round_end(context)
                break

            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                fn_reg = self.fn_map[fn_name]
                args = json.loads(tool_call.function.arguments)
                print(f'[{self.name}] Calling {fn_name}({args})\n')

                try:
                    if fn_reg.Params is not None:
                        res = fn_reg.fn(
                            fn_reg.Params(
                                _messages=context.raw(), **args
                            )
                        )
                    else:
                        res = fn_reg.fn()
                except Exception as e:
                    res = f'Error: {str(e)}'

                context.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fn_name,
                        "content": res,
                    }
                )
                self.on_round_end(context)

        return response_message.content