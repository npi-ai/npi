import asyncio
import itertools
import functools
from typing import Callable, Any


def default_get_context(args, kwargs):
    from npiai import Context

    for arg in itertools.chain(args, kwargs.values()):
        if isinstance(arg, Context):
            return arg
    return None


def with_checkpoint(
    _fn: Callable = None,
    checkpoint: Any = None,
    get_context=default_get_context,
):
    def decorator(fn: Callable):
        if asyncio.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def awrapper(*args, **kwargs):
                ctx = get_context(args, kwargs)

                if not ctx:
                    return await fn(*args, **kwargs)

                with ctx.checkpoint(checkpoint or fn.__qualname__):
                    return await fn(*args, **kwargs)

            return awrapper

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            ctx = get_context(args, kwargs)

            if not ctx:
                return fn(*args, **kwargs)

            with ctx.checkpoint(checkpoint or fn.__qualname__):
                return fn(*args, **kwargs)

        return wrapper

    if callable(_fn):
        return decorator(_fn)

    return decorator
