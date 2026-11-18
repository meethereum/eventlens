"""
In-memory run store keyed by run_id.
Holds completed RunContext objects so the inspect endpoint can retrieve card data
without re-running the analysis.  Capped at 50 runs (LRU eviction).
"""
from __future__ import annotations

from collections import OrderedDict
from threading import Lock

from app.core.events import RunContext

_MAX = 50
_store: OrderedDict[str, RunContext] = OrderedDict()
_lock = Lock()


def put(ctx: RunContext) -> None:
    with _lock:
        if ctx.run_id in _store:
            _store.move_to_end(ctx.run_id)
        else:
            _store[ctx.run_id] = ctx
            if len(_store) > _MAX:
                _store.popitem(last=False)


def get(run_id: str) -> RunContext | None:
    with _lock:
        return _store.get(run_id)
