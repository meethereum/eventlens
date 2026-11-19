"""
Fixture replay engine.

Loads a fixture JSON file and streams its events with realistic timing,
injecting the caller's run_id so the frontend can correlate events.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import AsyncIterator

from app.core.events import RunContext, SSEEvent

FIXTURE_DIR = Path(__file__).parent.parent.parent / "fixtures"
logger = logging.getLogger("eventlens.fixtures")

# ---------------------------------------------------------------------------
# Fixture selection
# ---------------------------------------------------------------------------

# Map (ticker, as_of) → fixture file stem
_FIXTURE_MAP: dict[tuple[str, str], str] = {
    ("INTC", "2024-12-02"): "intc_2024_12_02",
    ("XOM",  "2022-02-25"): "xom_2022_02_25",
    ("JPM",  "2023-03-13"): "jpm_2023_03_13",
    ("NVDA", "2025-01-28"): "nvda_2025_01_28",
}

# Queries that trigger the refusal fixture regardless of ticker.
# Patterns are (regex-style) checked as whole-word / phrase boundaries
# to avoid false positives like "what should I expect" matching "should i".
_ADVICE_PATTERNS = [
    "should i buy",
    "should i sell",
    "should i hold",
    "should i invest",
    "should i get",
    "should i purchase",
    "is it a good time to buy",
    "is it worth buying",
    "will the stock go up",
    "will the stock go down",
    "price target",
    "buy or sell",
]


def find_fixture(query: str, ticker: str, as_of: str) -> Path | None:
    """Return the fixture Path for this query, or None if not found."""
    q = query.lower()
    # Check for investment-advice intent using multi-word phrases only
    if any(pattern in q for pattern in _ADVICE_PATTERNS):
        return FIXTURE_DIR / "refusal_advice.json"
    key = (ticker.upper(), as_of)
    stem = _FIXTURE_MAP.get(key)
    if stem:
        return FIXTURE_DIR / f"{stem}.json"
    return None


def list_fixtures() -> list[dict]:
    """Return metadata for all available fixtures (for health endpoint)."""
    out = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        try:
            meta = json.loads(path.read_text())["meta"]
            out.append({"file": path.name, **meta})
        except Exception:
            pass
    return out


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------

async def replay_fixture(
    fixture_path: Path,
    ctx: RunContext,
) -> AsyncIterator[str]:
    """
    Async-generate SSE message strings from a fixture file.
    Respects each event's delay_ms for realistic pacing.
    Injects ctx.run_id into every event.
    Also populates ctx.cards, ctx.aggregate, ctx.verdict as events arrive
    so the run_store has a complete snapshot when streaming ends.
    """
    raw = json.loads(fixture_path.read_text())
    ctx.is_fixture = True
    ctx.event_evidence = raw.get("meta", {}).get("event_evidence", {})
    events: list[dict] = raw["events"]

    for ev in events:
        delay = ev.get("delay_ms", 0) / 1000.0
        if delay > 0:
            await asyncio.sleep(delay)

        event_type = ev["type"]
        data = ev.get("data", {})

        # Older fixtures contain legacy verdict prose with symbols and technical jargon.
        # The final verdict is rebuilt from the plain findings below.
        if event_type == "verdict_delta":
            continue

        if event_type == "card_done":
            try:
                from app.cards.plain_language import enrich_card
                from app.core.models import CardOutput

                card = CardOutput(**data["card"])
                data = {"card": enrich_card(card, ctx.ticker).model_dump()}
            except Exception as exc:
                logger.warning("Could not convert a demo finding to plain language: %s", exc)

        if event_type == "verdict_done":
            from app.llm.synthesis import _build_fallback

            parsed = ctx.parsed
            data = {
                "verdict": _build_fallback(
                    ctx.query,
                    {
                        "ticker": ctx.ticker,
                        "event_type": parsed.event_type if parsed else "company event",
                        "horizon_days": ctx.horizon_days,
                    },
                    ctx.cards,
                    ctx.aggregate,
                    [],
                ).model_dump(),
            }

        # Fixture files contain the ID from their original recording.  A replay
        # has a fresh run ID, so keep the payload in sync with the SSE envelope
        # used by API consumers.
        if event_type == "done":
            data = {**data, "run_id": ctx.run_id}

        # Populate run context for inspect endpoint
        _update_ctx(ctx, event_type, data)
        if event_type == "done":
            from app.core.run_store import put
            put(ctx)

        sse = SSEEvent(
            type=event_type,  # type: ignore[arg-type]
            run_id=ctx.run_id,
            ts=time.time(),
            data=data,
        )
        yield sse.to_sse()


def _update_ctx(ctx: RunContext, event_type: str, data: dict) -> None:
    """Side-effect: keep ctx up to date as events arrive."""
    if event_type == "query_parsed":
        from app.core.models import ParsedQuery
        try:
            ctx.parsed = ParsedQuery(**data["parsed"])
            ctx.ticker = ctx.parsed.ticker
            ctx.as_of = ctx.parsed.as_of
            ctx.horizon_days = ctx.parsed.horizon_days
        except Exception:
            pass

    elif event_type == "card_done":
        from app.core.models import CardOutput
        try:
            card = CardOutput(**data["card"])
            ctx.cards[card.id] = card
        except Exception:
            pass

    elif event_type == "aggregate":
        from app.core.models import AggregateResult
        try:
            ctx.aggregate = AggregateResult(**data["result"])
        except Exception:
            pass

    elif event_type == "verdict_done":
        from app.core.models import VerdictOutput
        try:
            ctx.verdict = VerdictOutput(**data["verdict"])
        except Exception:
            pass
