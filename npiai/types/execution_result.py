from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionResult:
    task: str
    result: str
