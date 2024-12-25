import asyncio
from typing import Callable, Awaitable, Any, AsyncGenerator


async def concurrent_task_runner[
    T
](
    fn: Callable[[asyncio.Queue[T]], Awaitable[Any]],
    concurrency: int = 1,
) -> AsyncGenerator[T, None]:
    # results queue
    results_queue: asyncio.Queue[T] = asyncio.Queue()
    # number of running tasks
    running_task_count = 0
    # lock for the counter
    counter_lock = asyncio.Lock()

    async def process():
        await fn(results_queue)

    async def task_runner():
        nonlocal running_task_count
        async with counter_lock:
            running_task_count += 1

        await process()

        async with counter_lock:
            running_task_count -= 1

    # schedule tasks
    tasks = [asyncio.create_task(task_runner()) for _ in range(concurrency)]

    # wait for the first task to start
    while running_task_count == 0:
        await asyncio.sleep(0.1)

    # collect results
    while running_task_count > 0 or not results_queue.empty():
        res = await results_queue.get()
        yield res

    # wait for all tasks to finish
    await asyncio.gather(*tasks)

    # consume the remaining items if any
    while not results_queue.empty():
        res = await results_queue.get()
        yield res
