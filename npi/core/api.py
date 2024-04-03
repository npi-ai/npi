"""the basic interface for the natural language programming interface"""
from abc import ABC, abstractmethod


class App(ABC):
    """the basic interface for the natural language programming interface"""

    @abstractmethod
    def chat(self, message, context=None) -> str:
        """the chat function for the app"""
