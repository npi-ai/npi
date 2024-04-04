from npi.app.google.gmail.shared.agent import Agent, FunctionRegistration
from npi.app.google.gmail.shared.gmail_extended import GmailExtended
from typing import List


class GmailAgent(Agent):
    gmail_client: GmailExtended

    def __init__(
        self,
        model: str = 'gpt-4-turbo-preview',
        api_key: str = None,
        function_list: List[FunctionRegistration] = None,
    ):
        super().__init__(
            model,
            api_key,
            system_prompt='You are a Gmail Agent helping users to manage their emails.',
            function_list=function_list,
        )
        self.gmail_client = GmailExtended(client_secret_file='./credentials.json')
