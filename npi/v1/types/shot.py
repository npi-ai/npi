from dataclasses import dataclass


@dataclass
class Shot:
    instruction: str
    calling: str
    output: str
