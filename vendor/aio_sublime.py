from __future__ import annotations
import asyncio
import sublime

from functools import wraps
from threading import Thread

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from concurrent.futures import Future
    from typing import Awaitable, Callable, Coroutine, Optional, TypedDict

__loop: Optional[asyncio.AbstractEventLoop] = None
__thread: Optional[Thread] = None


def asyncio_completions(func: Callable):
    """
    Decorate ST's completion query handler to dispatch them on asyncio event loop.

    Creates and immediately returns a `sublime.CompletionList`, applying results
    once `on_query_completions` has finished executing in ST's worker thread.

    Example:

    ```py
    class MyListener(sublime_plugin.EventListener):

        @asyncio_completions
        async def on_query_completions(self, view):
            ...
            return list(completions)
    ```
    """

    async def query_completions(
        completion_list: sublime.CompletionList, func: Callable, *args, **kwargs
    ):
        try:
            completions = await func(*args, **kwargs)
            if completions:
                flags = sublime.AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS
            else:
                flags = sublime.AutoCompleteFlags.NONE
                completions = []
        except Exception:
            completion_list.set_completions([])
            raise
        else:
            completion_list.set_completions(completions, flags)

    @wraps(func)
    def wrapper(*args, **kwargs):
        completion_list = sublime.CompletionList()
        run_coro(query_completions(completion_list, func, *args, **kwargs))
        return completion_list

    return wrapper


def asyncio_event(func: Callable):
    """
    Decorate ST event handler methods to dispatch them on asyncio event loop.

    Example:

    ```py
    class MyListener(sublime_plugin.EventListener):

        @asyncio_event
        async def on_modified(self, view):
            ...
    ```
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        run_coro(func(*args, **kwargs))

    return wrapper


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
        for task in asyncio.all_tasks():
            task.cancel()
        asyncio.get_event_loop().stop()

    if loop and thread:
        asyncio.run_coroutine_threadsafe(__shutdown(), loop)
        thread.join()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
