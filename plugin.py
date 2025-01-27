from __future__ import annotations
import asyncio
import simdjson
import sublime_plugin

from . import sublime_aio


def plugin_loaded():
    sublime_aio.setup_event_loop()


def plugin_unloaded():
    sublime_aio.shutdown_event_loop()


class CompletionListener1(sublime_plugin.ViewEventListener):

    @sublime_aio.completion
    async def on_query_completions(self, prefix, locations):
        await asyncio.sleep(1.0)
        return ["foo", "bar"]

    @sublime_aio.coro
    async def on_modified(self):
        print(f"{self.view!r} got modified on io loop!")
