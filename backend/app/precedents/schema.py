from __future__ import annotations

import math
from datetime import date
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

SUPPORTED_TICKERS = {
    "NVDA", "INTC", "AAPL", "MSFT", "GM", "SBUX", "AMZN", "DIS",
    "BA", "RTX", "XOM", "CVX", "JPM", "SCHW", "UNH",
}
ENTITIES = ("stock", "sector", "spy")
WINDOW_DAYS = (5, 20, 60)
PLACEHOLDER_TERMS = (
    "placeholder", "todo", "example.com", "example.org", "example.net",
    "scripted scenario", "not included", "unknown source", "eventlens",
)


class SourceRecord(BaseModel):
    title: str = Field(min_length=8)
    url: HttpUrl

    @model_validator(mode="after")
    def verify_source(self) -> "SourceRecord":
        url = str(self.url)
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("source URL must be an absolute HTTPS URL")
        if parsed.hostname.lower() in {"localhost", "example.com", "example.org", "example.net"}:
            raise ValueError("source URL uses a reserved placeholder host")
        text = f"{self.title} {url}".lower()
        if any(term in text for term in PLACEHOLDER_TERMS):
            raise ValueError("source title or URL contains a placeholder")
        return self


class OutcomePoint(BaseModel):
    day: int = Field(ge=0, le=60)
    date: date
    value: float = Field(gt=0)

    @model_validator(mode="after")
    def finite_value(self) -> "OutcomePoint":
        if not math.isfinite(self.value):
            raise ValueError("outcome values must be finite")
        return self


class ReturnWindows(BaseModel):
    d5: float
    d20: float
    d60: float

    @model_validator(mode="after")
    def finite_returns(self) -> "ReturnWindows":
        if not all(math.isfinite(value) for value in self.model_dump().values()):
            raise ValueError("outcome returns must be finite")
        return self


class EntityOutcomes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    returns: dict[Literal["stock", "sector", "spy"], ReturnWindows]
    series: dict[Literal["stock", "sector", "spy"], list[OutcomePoint]]

    @model_validator(mode="after")
    def complete_windows(self) -> "EntityOutcomes":
        if set(self.returns) != set(ENTITIES) or set(self.series) != set(ENTITIES):
            raise ValueError("outcomes must include stock, sector, and spy")
        for entity in ENTITIES:
            points = self.series[entity]
            if len(points) != 61 or [point.day for point in points] != list(range(61)):
                raise ValueError(f"{entity} outcome series must include trading days 0 through 60")
            if points[0].value != 100:
                raise ValueError(f"{entity} outcome series must be normalized to 100 on day 0")
            if any(points[i].date >= points[i + 1].date for i in range(60)):
                raise ValueError(f"{entity} outcome dates must be strictly increasing")
            for days in WINDOW_DAYS:
                expected = (points[days].value - 100)
                actual = getattr(self.returns[entity], f"d{days}")
                if abs(expected - actual) > 0.02:
                    raise ValueError(f"{entity} day-{days} return does not match the normalized series")
        stock_dates = [point.date for point in self.series["stock"]]
        if any([point.date for point in self.series[entity]] != stock_dates for entity in ("sector", "spy")):
            raise ValueError("stock, sector, and SPY outcomes must use aligned trading dates")
        return self


class PrecedentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=3)
    event_date: date
    ticker: str
    sector: str = Field(min_length=2)
    sector_etf: str = Field(min_length=1)
    event_type: str = Field(min_length=3)
    category: str = Field(min_length=3)
    market_mood: Literal["risk_on", "risk_off", "mixed"]
    summary: str = Field(min_length=30)
    source: SourceRecord
    outcomes: EntityOutcomes

    @model_validator(mode="after")
    def validate_event(self) -> "PrecedentRecord":
        if self.ticker not in SUPPORTED_TICKERS:
            raise ValueError(f"unsupported ticker: {self.ticker}")
        if not date(2015, 1, 1) <= self.event_date <= date(2025, 12, 31):
            raise ValueError("event date must be in 2015–2025")
        if any(term in self.summary.lower() for term in PLACEHOLDER_TERMS):
            raise ValueError("summary contains placeholder text")
        return self
