from dataclasses import dataclass


@dataclass
class Example:
    instruction: str = None
    calling: str = None
    output: str = None
