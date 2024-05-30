from typing import List, Callable, Awaitable
from npiai.utils import to_async_fn


class Hooks:
    _start_callbacks: List[Callable[[], Awaitable]]
    _end_callbacks: List[Callable[[], Awaitable]]

    def __init__(self):
        self._start_callbacks = []
        self._end_callbacks = []

    def on_start(self, callback: Callable):
        """
        Bootstrap function decorator

        Args:
            callback: Callback function which will be executed when starting
        """
        wrapped_callback = to_async_fn(callback)
        self._start_callbacks.append(wrapped_callback)
        return wrapped_callback

    def on_end(self, callback: Callable):
        """
        Cleanup function decorator

        Args:
            callback: Callback function which will be executed when ending
        """
        wrapped_callback = to_async_fn(callback)
        self._end_callbacks.append(wrapped_callback)
        return wrapped_callback

    # internal methods

    async def internal_start(self):
        for cb in self._start_callbacks:
            await cb()

    async def internal_end(self):
        for cb in self._end_callbacks:
            await cb()
