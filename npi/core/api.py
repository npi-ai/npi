from abc import ABC, abstractmethod

class App(ABC):
    @abstractmethod
    def chat(self, context=None, message="") -> str:
        pass