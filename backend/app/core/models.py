"""
Shared Pydantic models used across the application.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Card models
# ---------------------------------------------------------------------------

class CardStatus(str, Enum):
    queued   = "queued"
    fetching = "fetching"
    done     = "done"
    error    = "error"

    def __str__(self) -> str:
        return self.value


class SignalLabel(str, Enum):
    tailwind = "tailwind"
    neutral  = "neutral"
    headwind = "headwind"

    def __str__(self) -> str:
        return self.value


class Headline(BaseModel):
    label: str
    value: float | str
    unit: str = ""
    delta: float | None = None


class Metric(BaseModel):
    name: str
    value: float | str | None
    unit: str = ""
    note: str = ""


class Series(BaseModel):
    t: str  # ISO date string
    v: float | None


class MathDetail(BaseModel):
    formula: str
    inputs: dict[str, Any]
    contribution: float | None = None


class Source(BaseModel):
    name: str
    url: str
    retrieved_at: str


class CardOutput(BaseModel):
    id: str
    title: str
    status: CardStatus = CardStatus.queued
    as_of: str = ""
    fetched_at: str = ""
    latency_ms: int = 0

    headline: Headline | None = None
    metrics: list[Metric] = []
    series: list[Series] = []

    signal: float = 0.0          # s in [-1, 1]
    label: SignalLabel = SignalLabel.neutral
    weight: float = 0.6          # w in [0, 1]
    quality: float = 1.0         # q in [0, 1]

    reasoning: list[str] = []    # 3-5 plain-English strings
    math: MathDetail | None = None
    sources: list[Source] = []
    warnings: list[str] = []

    error_message: str | None = None


# ---------------------------------------------------------------------------
# Query models
# ---------------------------------------------------------------------------

class ParsedQuery(BaseModel):
    ticker: str
    event_type: str
    as_of: str          # ISO date
    horizon_days: int = 20
    intent: str = "analysis"   # analysis | advice_request | out_of_scope


# ---------------------------------------------------------------------------
# Aggregate / verdict models
# ---------------------------------------------------------------------------

class ScenarioScore(BaseModel):
    name: str
    score: float
    ci_low: float
    ci_high: float
    rationale: str = ""
    watch_for: str = ""


class AggregateResult(BaseModel):
    composite_signal: float
    evidence_strength: float
    coverage: float
    scenarios: list[ScenarioScore]
    card_contributions: dict[str, float]   # card_id -> contribution


class VerdictOutput(BaseModel):
    headline: str
    summary: str
    key_drivers: list[dict[str, str]] = []
    counter_evidence: list[dict[str, str]] = []
    scenarios: list[dict[str, Any]] = []
    confidence_statement: str = ""
    data_gaps: list[str] = []
    disclaimer: str = ""
    references: list[Source] = []
    is_fallback: bool = False          # True when LLM failed; template used
    model_used: str = ""
    is_fallback_model: bool = False    # True when fallback model was used


# ---------------------------------------------------------------------------
# Health models
# ---------------------------------------------------------------------------

class DataSourceHealth(BaseModel):
    name: str
    status: str    # live | cached | demo | error
    last_updated: str | None = None
    note: str = ""


class HealthResponse(BaseModel):
    status: str    # ok | degraded | demo
    demo_mode: bool
    missing_keys: list[str]
    llm_base_url_host: str
    llm_model: str
    llm_model_available: bool | None = None   # None = not checked yet
    data_sources: list[DataSourceHealth]
    version: str = "0.1.0"
