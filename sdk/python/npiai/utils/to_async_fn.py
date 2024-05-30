from typing import Callable, Awaitable
import functools
import asyncio


def to_async_fn(fn: Callable) -> Callable[..., Awaitable]:
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        res = fn(*args, **kwargs)
        if asyncio.iscoroutine(res):
            return await res
        return res

    return wrapper
