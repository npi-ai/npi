from dataclasses import dataclass


@dataclass
class Shot:
    instruction: str = None
    calling: str = None
    output: str = None
