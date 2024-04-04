from dataclasses import dataclass
from typing import Callable, Any, Type, TYPE_CHECKING

from npi.app.google.gmail.shared.parameter import Parameter

if TYPE_CHECKING:
    from npi.app.google.gmail.shared.agent import Agent

AgentFunction = Callable[[Parameter, 'Agent', str], Any | None]


@dataclass
class FunctionRegistration:
    fn: AgentFunction
    description: str
    Params: Type[Parameter]
    name: str = None

    def __init__(
        self,
        fn: AgentFunction,
        description: str,
        Params: Type[Parameter],
        name: str = None,
    ):
        self.fn = fn
        self.description = description
        self.Params = Params

        if name is None:
            self.name = f'{fn.__name__}_{hash(fn)}'
        else:
            self.name = name
