# AsyncIO for Sublime Text

This package demonstrates power of asyncio and [simdjson](https://pypi.org/project/pysimdjson/)
to handle hundrets of thousands of completions smoothly,
without blocking Sublime Text's UI in any way.

It also show cases how to turn any ST event handler
into an asyncio coroutine by just decorating it.

```py
from __future__ import annotations
import simdjson
import sublime_plugin

from .vendor import aio_sublime


def plugin_loaded():
    aio_sublime.setup_event_loop()


def plugin_unloaded():
    aio_sublime.shutdown_event_loop()


class CompletionListener(sublime_plugin.ViewEventListener):
    parser = simdjson.Parser()

    @aio_sublime.asyncio_completions
    async def on_query_completions(self, prefix, locations):
        doc = self.parser.parse(data)
        return (i["label"] for i in doc["items"])

    @aio_sublime.asyncio_event
    async def on_modified(self):
        print(f"{self.view!r} got modified on io loop!")
```
