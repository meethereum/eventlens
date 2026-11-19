"""
Analysis pipeline entry point.

Demo mode  → fixture replay
Live mode  → LLM parsing + real card fetches + LLM synthesis
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import AsyncIterator

from app.core.config import get_settings
from app.core.events import RunContext, SSEEvent
from app.core.fixture_engine import find_fixture, replay_fixture

logger = logging.getLogger("eventlens.pipeline")

# Covered ticker universe
COVERED_TICKERS = {
    "NVDA", "INTC", "AAPL", "MSFT",
    "GM", "SBUX", "AMZN",
    "DIS",
    "BA", "RTX",
    "XOM", "CVX",
    "JPM", "SCHW",
    "UNH",
}

_ADVICE_PATTERNS = [
    "should i buy", "should i sell", "should i hold", "should i invest",
    "buy or sell", "is it a good time to buy", "price target",
    "will the stock go up", "will the stock go down",
]


async def run_analysis(
    query: str,
    ticker: str,
    as_of: str,
    run_id: str | None = None,
) -> AsyncIterator[str]:
    cfg = get_settings()
    ctx = RunContext(
        run_id=run_id or str(uuid.uuid4()),
        query=query,
        ticker=ticker.upper(),
        as_of=as_of,
    )

    # Always try fixture first
    fixture_path = find_fixture(query, ticker, as_of)
    if fixture_path and fixture_path.exists():
        async for chunk in replay_fixture(fixture_path, ctx):
            yield chunk
        from app.core.run_store import put
        put(ctx)
        return

    # Demo mode without matching fixture
    if cfg.is_demo_mode:
        async for chunk in _not_in_fixture_response(ctx):
            yield chunk
        return

    # Live mode
    async for chunk in _live_analysis(ctx):
        yield chunk
    from app.core.run_store import put
    put(ctx)


async def _live_analysis(ctx: RunContext) -> AsyncIterator[str]:
    """Full live pipeline: LLM parse → scope check → cards → aggregate → LLM synthesise."""
    from app.cards.registry import CARDS
    from app.llm.parsing import parse_query
    from app.llm.synthesis import synthesize_verdict
    import concurrent.futures

    loop = asyncio.get_event_loop()

    # ── LLM call 1: parse query ───────────────────────────────────────────
    parsed = await loop.run_in_executor(
        None, parse_query, ctx.query, ctx.ticker, ctx.as_of
    )

    ctx.ticker = parsed["ticker"].upper()
    ctx.as_of  = parsed["as_of"]
    ctx.horizon_days = parsed["horizon_days"]

    yield SSEEvent(
        type="query_parsed",
        run_id=ctx.run_id,
        ts=time.time(),
        data={
            "parsed": {
                "ticker": parsed["ticker"],
                "event_type": parsed["event_type"],
                "as_of": parsed["as_of"],
                "horizon_days": parsed["horizon_days"],
                "intent": parsed["intent"],
            },
            "latency_ms": parsed["latency_ms"],
        },
    ).to_sse()

    await asyncio.sleep(0.05)

    # ── Scope check ───────────────────────────────────────────────────────
    ticker = ctx.ticker
    intent = parsed["intent"]

    if intent == "advice_request":
        from app.core.run_store import put
        put(ctx)
        yield SSEEvent(
            type="scope_check",
            run_id=ctx.run_id,
            ts=time.time(),
            data={
                "in_scope": False,
                "ticker": ticker,
                "reason": "intent is advice_request",
                "refusal_message": (
                    "EventLens is a descriptive analysis tool — it explains what financial and macro "
                    "factors are at play, not whether to buy or sell. "
                    "Try asking about a specific event: 'Intel's CEO was just ousted. What should I expect?'"
                ),
            },
        ).to_sse()
        yield SSEEvent(type="done", run_id=ctx.run_id, ts=time.time(),
                       data={"run_id": ctx.run_id, "total_ms": ctx.elapsed_ms()}).to_sse()
        return

    if intent == "out_of_scope":
        from app.core.run_store import put
        put(ctx)
        yield SSEEvent(
            type="scope_check",
            run_id=ctx.run_id,
            ts=time.time(),
            data={
                "in_scope": False,
                "ticker": ticker,
                "reason": "intent is out_of_scope",
                "refusal_message": (
                    "EventLens analyses specific company events (CEO changes, earnings, macro shocks). "
                    "Please ask about a specific company and event."
                ),
            },
        ).to_sse()
        yield SSEEvent(type="done", run_id=ctx.run_id, ts=time.time(),
                       data={"run_id": ctx.run_id, "total_ms": ctx.elapsed_ms()}).to_sse()
        return

    in_scope = ticker in COVERED_TICKERS
    yield SSEEvent(
        type="scope_check",
        run_id=ctx.run_id,
        ts=time.time(),
        data={
            "in_scope": in_scope,
            "ticker": ticker,
            "reason": "ticker in covered universe" if in_scope else "ticker not in covered universe",
            "refusal_message": (
                "" if in_scope else
                f"{ticker} is not in the EventLens v1 covered universe. "
                "Covered: NVDA, INTC, AAPL, MSFT, GM, SBUX, AMZN, DIS, BA, RTX, XOM, CVX, JPM, SCHW, UNH."
            ),
        },
    ).to_sse()

    if not in_scope:
        from app.core.run_store import put
        put(ctx)
        yield SSEEvent(type="done", run_id=ctx.run_id, ts=time.time(),
                       data={"run_id": ctx.run_id, "total_ms": ctx.elapsed_ms()}).to_sse()
        return

    # ── Fetch cards concurrently ──────────────────────────────────────────
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(CARDS))

    for card_id, card_title, _ in CARDS:
        await asyncio.sleep(0.03)
        yield SSEEvent(
            type="card_start",
            run_id=ctx.run_id,
            ts=time.time(),
            data={"card_id": card_id, "title": card_title},
        ).to_sse()

    futures: dict[str, asyncio.Future] = {}
    for card_id, card_title, fetch_fn in CARDS:
        futures[card_id] = loop.run_in_executor(executor, fetch_fn, ctx.ticker, ctx.as_of)

    for card_id, future in futures.items():
        try:
            card = await future
            ctx.cards[card_id] = card
            yield SSEEvent(
                type="card_done",
                run_id=ctx.run_id,
                ts=time.time(),
                data={"card": card.model_dump()},
            ).to_sse()
        except Exception as exc:
            logger.warning("Card %s failed: %s", card_id, exc)
            yield SSEEvent(
                type="card_error",
                run_id=ctx.run_id,
                ts=time.time(),
                data={"card_id": card_id, "title": card_id, "error": str(exc)},
            ).to_sse()

    # ── Aggregate (M5 math) ───────────────────────────────────────────────
    agg = _compute_aggregate(ctx)
    ctx.aggregate = agg
    yield SSEEvent(
        type="aggregate",
        run_id=ctx.run_id,
        ts=time.time(),
        data={"result": agg.model_dump()},
    ).to_sse()

    # ── LLM call 2: synthesise verdict ───────────────────────────────────
    from app.precedents.engine import find_precedents
    c4 = ctx.cards.get("C4")
    market_mood = "risk_off" if c4 and c4.signal < -0.1 else "risk_on" if c4 and c4.signal > 0.1 else "mixed"
    historical_precedents = find_precedents(
        ctx.ticker,
        parsed["event_type"],
        ctx.as_of,
        market_mood=market_mood,
    )
    verdict, is_verified = await loop.run_in_executor(
        None,
        synthesize_verdict,
        ctx.query,
        parsed,
        ctx.cards,
        ctx.aggregate,
        historical_precedents,
    )
    ctx.verdict = verdict

    # Stream summary word by word
    text_to_stream = verdict.summary
    for word in text_to_stream.split():
        await asyncio.sleep(0.04)
        yield SSEEvent(
            type="verdict_delta",
            run_id=ctx.run_id,
            ts=time.time(),
            data={"delta": word + " "},
        ).to_sse()

    yield SSEEvent(
        type="verdict_done",
        run_id=ctx.run_id,
        ts=time.time(),
        data={"verdict": verdict.model_dump()},
    ).to_sse()

    from app.core.run_store import put
    put(ctx)
    yield SSEEvent(
        type="done",
        run_id=ctx.run_id,
        ts=time.time(),
        data={"run_id": ctx.run_id, "total_ms": ctx.elapsed_ms()},
    ).to_sse()


def _compute_aggregate(ctx: RunContext):
    from app.core.models import AggregateResult, ScenarioScore
    from app.scoring.aggregate import aggregate_from_cards

    cards = list(ctx.cards.values())
    result = aggregate_from_cards(cards)

    scenarios = [
        ScenarioScore(
            name=result.scenario_names[i],
            score=result.scenario_scores[i],
            ci_low=result.scenario_ci_low[i],
            ci_high=result.scenario_ci_high[i],
            rationale="",
            watch_for="",
        )
        for i in range(3)
    ]

    return AggregateResult(
        composite_signal=result.composite_signal,
        evidence_strength=result.evidence_strength,
        coverage=result.coverage,
        scenarios=scenarios,
        card_contributions=result.card_contributions,
    )


async def _not_in_fixture_response(ctx: RunContext) -> AsyncIterator[str]:
    await asyncio.sleep(0.3)
    yield SSEEvent(
        type="query_parsed",
        run_id=ctx.run_id,
        ts=time.time(),
        data={
            "parsed": {
                "ticker": ctx.ticker or "UNKNOWN",
                "event_type": "unknown",
                "as_of": ctx.as_of or "today",
                "horizon_days": 20,
                "intent": "analysis",
            },
            "latency_ms": 280,
        },
    ).to_sse()

    await asyncio.sleep(0.1)
    yield SSEEvent(
        type="scope_check",
        run_id=ctx.run_id,
        ts=time.time(),
        data={
            "in_scope": False,
            "ticker": ctx.ticker or "",
            "reason": "no_fixture",
            "refusal_message": (
                "EventLens is running in demo mode and this query doesn't match one of the four scripted demos. "
                "Try: \"Intel's CEO was just ousted. What should I expect?\" (INTC, 2024-12-02), "
                "\"Russia has invaded Ukraine and oil is spiking. How does that affect Exxon?\" (XOM, 2022-02-25), "
                "\"Silicon Valley Bank just collapsed. What does that mean for JPMorgan?\" (JPM, 2023-03-13), or "
                "\"Nvidia fell sharply after the DeepSeek news. Is that company-specific or sector-wide?\" (NVDA, 2025-01-28)."
            ),
        },
    ).to_sse()

    await asyncio.sleep(0.05)
    yield SSEEvent(
        type="done",
        run_id=ctx.run_id,
        ts=time.time(),
        data={"run_id": ctx.run_id, "total_ms": ctx.elapsed_ms()},
    ).to_sse()
