from typing import Callable, Type, Optional, Awaitable
import re
import asyncio
from npi.types.parameters import Parameters

ToolFunction = Callable[[Parameters], str | None | Awaitable[str | None]]


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
        # wrap fn in an async wrapper
        async def func(*args, **kwargs):
            res = fn(*args, **kwargs)
            if asyncio.iscoroutine(res):
                return await res
            return res

        self.fn = func
        self.description = description
        self.Params = Params

        if name is None:
            self.name = fn.__name__
        else:
            self.name = name
