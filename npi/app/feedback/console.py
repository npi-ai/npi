
from npi.core.api import App


class HumanFeedback(App):
    """the function wrapper of HumanFeedback App"""

    __human_funcs = {
        "ask": {
            "name": "ask",
            "description": "ask the user for the information",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "the question you want to ask the user"
                    },
                },
                "required": ["question"],
            },
        },
        "confirm": {
            "name": "confirm",
            "description": "confirm the information with the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "the message you want to confirm with the user"
                    },
                },
                "required": ["message"],
            },
        },
        "provide": {
            "name": "provide",
            "description": "provide the information to the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "the message you want to provide to the user"
                    },
                },
                "required": ["message"],
            },
        },
    }

    def __init__(self):
        super().__init__(
            name="human",
            description="if you think other tools can't help you, you can ask the human for help by use this tool.",
            llm=None,
            mode="gpt-4-turbo-preview",
            tool_choice="auto"
        )
        self._register_functions(self.__human_funcs)

    def chat(self, message, context=None) -> str:
        return input(message)
