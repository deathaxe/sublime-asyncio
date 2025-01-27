from __future__ import annotations
import asyncio
import sublime
import traceback

from functools import wraps
from threading import Thread

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from concurrent.futures import Future
    from typing import Callable

__all__ = ["completion", "coro"]

from .event_loop import run_coro


async def query_completions(
    req_id: int,
    completion_list: sublime.CompletionList,
    func: Callable,
    *args,
    **kwargs,
):
    try:
        completions = await func(*args, **kwargs)
        if completions:
            flags = sublime.AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS
            print(f"query {req_id} completed")
        else:
            flags = sublime.AutoCompleteFlags.NONE
            completions = []
            print(f"query {req_id} completed (empty)")
    except asyncio.CancelledError:
        completion_list.set_completions([])
        print(f"cancelled {req_id}")
    except Exception:
        completion_list.set_completions([])
        traceback.print_exc()
    else:
        completion_list.set_completions(completions, flags)


def completion(func: Callable):
    """
    Decorate ST's completion query handler to dispatch them on asyncio event loop.

    Creates and immediately returns a `sublime.CompletionList`, applying results
    once `on_query_completions` has finished executing in ST's worker thread.

    Example:

    ```py
    import sublime_aio

    class MyCompletions(sublime_plugin.EventListener):
        @sublime_aio.completion
        async def on_query_completions(self, view):
            ...
            return list(completions)
    ```
    """
    req_id = 0
    task = None

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal req_id, task

        req_id += 1
        print(f"new query: {req_id}")

        completion_list = sublime.CompletionList()

        if task:
            task.cancel()
        task = run_coro(
            query_completions(req_id, completion_list, func, *args, **kwargs)
        )
        return completion_list

    return wrapper


async def run(func: Callable, *args, **kwargs):
    try:
        return await func(*args, **kwargs)
    except Exception:
        traceback.print_exc()


def coro(func: Callable):
    """
    Decorate command or listener methods to dispatch them on asyncio event loop.

    Example:

    ```py
    import sublime_aio

    class MyListener(sublime_plugin.EventListener):
        @sublime_aio.coro
        async def on_modified(self, view):
            ...

    class MyAsyncCommand(sublime_plugin.WindowCommand):
        @sublime_aio.coro
        async def run(self):
            ...
    ```
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        run_coro(run(func, *args, **kwargs))

    return wrapper
