import itertools
import functools
from typing import Callable, Any

from npiai import Context

from .logger import logger
from .to_async_fn import to_async_fn


def with_checkpoint(checkpoint: Any):
    def decorator(fn: Callable):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            ctx = None

            async_fn = to_async_fn(fn)

            for arg in itertools.chain(args, kwargs.values()):
                if isinstance(arg, Context):
                    ctx = arg
                    break
            if not ctx:
                logger.warning("Context not found")
                return await async_fn(*args, **kwargs)

            try:
                ctx.checkpoint(checkpoint)
                return await async_fn(*args, **kwargs)
            finally:
                ctx.clear_checkpoint()

        return wrapper

    return decorator
