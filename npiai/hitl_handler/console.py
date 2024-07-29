import questionary

from termcolor import colored
from npiai.core import HITL
from npiai.context import Context


class ConsoleHandler(HITL):
    async def confirm(self, ctx: Context, tool_name: str, message: str) -> bool:
        # print(colored(f'[{tool_name}]: Confirmation required', color='green', attrs=['bold']))
        print(colored(f"[{tool_name}]: {message}", color="magenta", attrs=["bold"]))
        return await questionary.confirm("Continue?").ask_async()

    async def input(self, ctx: Context, tool_name: str, message: str) -> str:
        # print(colored(f'[{tool_name}]: Additional information required', color='green', attrs=['bold']))
        print(colored(f"[{tool_name}]: {message}", color="magenta", attrs=["bold"]))
        return await questionary.text("Type your response:").ask_async()
