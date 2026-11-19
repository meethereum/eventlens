"""
Shared Pydantic models used across the application.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    related_series: dict[str, list[Series]] = {}

    signal: float = 0.0          # s in [-1, 1]
    label: SignalLabel = SignalLabel.neutral
    weight: float = 0.6          # w in [0, 1]
    quality: float = 1.0         # q in [0, 1]

    reasoning: list[str] = []    # 3-5 plain-English strings
    math: MathDetail | None = None
    sources: list[Source] = []
    warnings: list[str] = []

    error_message: str | None = None
    plain_title: str = ""
    plain_summary: str = ""
    direction: Literal["against", "for", "neutral"] = "neutral"
    strength: Literal["strong", "moderate", "slight"] = "slight"


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


class OverviewPoint(BaseModel):
    title: str
    explanation: str
    findings: list[str]
    direction: Literal["against", "for"]
    strength: Literal["strong", "moderate", "slight"]


class OverviewWatchItem(BaseModel):
    what: str
    why: str
    findings: list[str]


class OverviewScenario(BaseModel):
    id: Literal["against", "mixed", "for"]
    name: str
    score: float = 0.0
    what_it_looks_like: str
    signs: str


class VerdictOutput(BaseModel):
    # ``model_used`` is part of the public response contract. Permit that
    # field name without Pydantic treating the ``model_`` prefix as reserved.
    model_config = ConfigDict(protected_namespaces=())

    headline: str = ""
    answer: str = ""
    how_sure_level: Literal["High", "Medium", "Low"] = "Low"
    how_sure_reason: str = ""
    points: list[OverviewPoint] = []
    unknowns: list[str] = []
    watch: list[OverviewWatchItem] = []
    scenarios: list[OverviewScenario] = []
    scenario_split: dict[str, float] = {}
    summary: str = ""  # legacy fixture compatibility
    key_drivers: list[dict[str, str]] = []
    counter_evidence: list[dict[str, str]] = []
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
