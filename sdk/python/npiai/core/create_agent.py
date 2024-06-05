from typing import overload

from npiai.llm import LLM
from .app import App
from .browser_app import BrowserApp
from npiai.core.app import Agent
from npiai.core.browser_app import BrowserAgent


@overload
def create_agent(app: App, llm: LLM = None) -> Agent:
    ...


@overload
def create_agent(app: BrowserApp, llm: LLM = None) -> BrowserAgent:
    ...


def create_agent(app: App | BrowserApp, llm: LLM = None) -> Agent | BrowserAgent:
    if isinstance(app, App):
        return Agent(app, llm)

    if isinstance(app, BrowserApp):
        return BrowserAgent(app, llm)

    raise TypeError(f'app must be an instance of App or BrowserApp')
