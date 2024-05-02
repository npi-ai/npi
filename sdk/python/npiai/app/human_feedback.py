from termcolor import colored

from npiai.core.base import App
from npiai_proto import api_pb2


class ConsoleFeedback(App):

    def __init__(self):
        super().__init__(
            app_name="console_feedback",
            app_type=api_pb2.AppType.APP_UNKNOWN,
        )

    def schema(self):
        return {
            "type": "function",
            "function": {
                "name": f"{self.tool_name()}",
                "description": "Ask the human for help",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": f"the task you want to ask for help",
                        },
                    },
                    "required": ["message"],
                },
            },
        }

    def chat(self, msg: str) -> str:
        print(colored(msg, 'green'))
        response = input(colored('Type Your Response: ', 'magenta'))
        print()
        return response

