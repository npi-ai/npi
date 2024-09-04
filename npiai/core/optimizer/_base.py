from abc import ABC, abstractmethod

from npiai.context import Context
from npiai.types import Plan


class BaseOptimizer(ABC):
    _rules: str | None = None

    def __init__(self, rules: str | None = None):
        self._rules = rules

    @abstractmethod
    async def optimize(self, ctx: Context, plan) -> Plan: ...
