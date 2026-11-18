"""
SSE event types and the run-context object passed through the pipeline.
Every event is serialised as JSON and sent as a single SSE `data:` line.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.core.models import (
    AggregateResult,
    CardOutput,
    ParsedQuery,
    VerdictOutput,
)

# ---------------------------------------------------------------------------
# SSE event envelope  (Pydantic model — serialised to JSON)
# ---------------------------------------------------------------------------

SSEEventType = Literal[
    "query_parsed",
    "scope_check",
    "card_start",
    "card_done",
    "card_error",
    "aggregate",
    "verdict_delta",
    "verdict_done",
    "done",
    "error",
]


class SSEEvent(BaseModel):
    type: SSEEventType
    run_id: str
    ts: float = Field(default_factory=time.time)
    data: Any = None

    model_config = {"arbitrary_types_allowed": True}

    def to_sse(self) -> str:
        """Format as a proper SSE message string."""
        return f"data: {self.model_dump_json()}\n\n"


# ---------------------------------------------------------------------------
# Typed payloads (used for documentation / validation; not strictly required
# since data is passed as plain dicts through the pipeline)
# ---------------------------------------------------------------------------

class QueryParsedPayload(BaseModel):
    parsed: ParsedQuery
    latency_ms: int


class ScopeCheckPayload(BaseModel):
    in_scope: bool
    ticker: str
    reason: str
    refusal_message: str = ""


class CardStartPayload(BaseModel):
    card_id: str
    title: str


class CardDonePayload(BaseModel):
    card: CardOutput


class CardErrorPayload(BaseModel):
    card_id: str
    title: str
    error: str


class AggregatePayload(BaseModel):
    result: AggregateResult


class VerdictDeltaPayload(BaseModel):
    delta: str


class VerdictDonePayload(BaseModel):
    verdict: VerdictOutput


class DonePayload(BaseModel):
    run_id: str
    total_ms: int


class ErrorPayload(BaseModel):
    message: str
    detail: str = ""


# ---------------------------------------------------------------------------
# Run context — threaded through the entire pipeline (plain dataclass)
# ---------------------------------------------------------------------------

@dataclass
class RunContext:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    parsed: ParsedQuery | None = None
    as_of: str = ""
    horizon_days: int = 20
    ticker: str = ""
    cards: dict[str, CardOutput] = field(default_factory=dict)
    aggregate: AggregateResult | None = None
    verdict: VerdictOutput | None = None
    started_at: float = field(default_factory=time.time)

    def elapsed_ms(self) -> int:
        return int((time.time() - self.started_at) * 1000)
