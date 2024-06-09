import questionary

from termcolor import colored
from npiai.core import HITL


class ConsoleHandler(HITL):
    async def confirm(self, app_name: str, message: str) -> bool:
        # print(colored(f'[{app_name}]: Confirmation required', color='green', attrs=['bold']))
        print(colored(f'[{app_name}]: {message}', color='magenta', attrs=['bold']))
        return await questionary.confirm('Continue?').ask_async()

    async def input(self, app_name: str, message: str) -> str:
        # print(colored(f'[{app_name}]: Additional information required', color='green', attrs=['bold']))
        print(colored(f'[{app_name}]: {message}', color='magenta', attrs=['bold']))
        return await questionary.text('Type your response:').ask_async()
