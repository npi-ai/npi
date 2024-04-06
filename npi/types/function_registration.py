from typing import Callable, Type, Optional
import re
from npi.types.parameters import Parameters

ToolFunction = Callable[[Parameters], str | None]


class FunctionRegistration:
    fn: ToolFunction
    description: str
    name: str
    Params: Optional[Type[Parameters]] = None

    def __init__(
        self,
        fn: ToolFunction,
        description: str,
        name: str = None,
        Params: Type[Parameters] = None,
    ):
        self.fn = fn
        self.description = description
        self.Params = Params

        if name is None:
            # remove the leading and trailing underscores from the function name
            self.name = f'{re.sub(r"^_+|_+$", "", fn.__name__)}_{hash(fn)}'
        else:
            self.name = name
