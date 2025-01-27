from __future__ import annotations
import asyncio

from functools import wraps
from threading import Thread

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from concurrent.futures import Future
    from typing import Coroutine

__all__ = [
    "run_coro",
    "setup_event_loop",
    "shutdown_event_loop"
]

__loop: asyncio.AbstractEventLoop | None = None
__thread: Thread | None = None


def run_coro(coro: Coroutine) -> Future:
    """
    Run coroutine from synchronous code.

    Example:

    ```py
    async def an_async_func(arg1, arg2):
        ...

    def sync_func(arg1, arg2):
        future = run_coro(an_async_func(arg1, arg2))
    ```
    """
    if not __loop:
        raise RuntimeError("No event loop running!")

    return asyncio.run_coroutine_threadsafe(coro, __loop)


def setup_event_loop():
    global __loop
    global __thread

    if __loop:
        # raise RuntimeError("Event loop already running!")
        return

    __loop = asyncio.new_event_loop()
    __thread = Thread(target=__loop.run_forever)
    __thread.start()


def shutdown_event_loop():
    global __loop
    global __thread

    if not __loop:
        # raise RuntimeError("No event loop to shutdown!")
        return

    thread = __thread
    __thread = None
    loop = __loop
    __loop = None

    async def __shutdown():
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.stop()

    if loop and thread:
        asyncio.run_coroutine_threadsafe(__shutdown(), loop)
        thread.join()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
