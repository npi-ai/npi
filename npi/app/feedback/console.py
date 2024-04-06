from typing import List, Tuple
from termcolor import colored
from openai.types.chat import ChatCompletionMessageParam
from npi.core.api import App, ChatParameters


class HumanFeedback(App):
    """the function wrapper of HumanFeedback App"""

    llm: None

    def __init__(self):
        super().__init__(
            name="human_feedback",
            description="Ask the human for help",
            llm=None,
            model="gpt-4-turbo-preview",
            tool_choice="auto"
        )

    def chat(
        self,
        message: str | ChatParameters,
        context: List[ChatCompletionMessageParam] = None,
        return_history: bool = False,
    ) -> str | Tuple[str, List[ChatCompletionMessageParam]]:
        prompt = message.task if isinstance(message, ChatParameters) else message
        response = input(colored(prompt, 'green') + colored('\nType Your Response: ', 'magenta'))
        print()

        if return_history:
            history = [
                *context,
                {
                    'role': 'user',
                    'content': response,
                },
            ]
            return response, history

        return response


__all__ = ["HumanFeedback"]
