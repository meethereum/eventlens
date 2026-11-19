"""
POST /api/analyze   — streams SSE events for the full analysis pipeline
GET  /api/analyze/status/{run_id}  — quick status check
GET  /api/cards/{card_id}/inspect?run_id=...  — full card detail
POST /api/simulate/explain — explicit, cached scenario explanation
"""
from __future__ import annotations

import time
import uuid
from datetime import date, datetime, timezone
from statistics import median
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.demo_router import run_analysis
from app.core.run_store import get as get_run
from app.precedents.engine import find_precedents
from app.scoring.aggregate import aggregate_from_cards
from app.scoring.simulation import (
    ScenarioOverrides as SimulationOverrides,
    build_presentation,
    simulate,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    query: str
    ticker: str = ""          # optional pre-parsed ticker; engine will parse if empty
    as_of: str = ""           # ISO date; defaults to today


# ---------------------------------------------------------------------------
# POST /api/analyze
# ---------------------------------------------------------------------------

@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    run_id = str(uuid.uuid4())
    as_of = req.as_of or date.today().isoformat()
    ticker = req.ticker.upper() if req.ticker else _extract_ticker_hint(req.query)

    async def event_generator():
        try:
            async for chunk in run_analysis(
                query=req.query,
                ticker=ticker,
                as_of=as_of,
                run_id=run_id,
            ):
                # chunk is already a full "data: {...}\n\n" string.
                # Yield it as raw bytes so EventSourceResponse doesn't
                # double-wrap it.
                yield chunk
        except Exception as exc:
            from app.core.events import SSEEvent
            yield SSEEvent(
                type="error",
                run_id=run_id,
                ts=time.time(),
                data={"message": str(exc), "detail": ""},
            ).to_sse()

    # media_type text/event-stream, no extra wrapping
    from starlette.responses import StreamingResponse
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# GET /api/cards/{card_id}/inspect
# ---------------------------------------------------------------------------

@router.get("/cards/{card_id}/inspect")
async def inspect_card(card_id: str, run_id: str = Query(default="")):
    if not run_id:
        return JSONResponse(status_code=400, content={"detail": "run_id is required"})

    ctx = get_run(run_id)
    if ctx is None:
        return JSONResponse(status_code=404, content={"detail": f"run {run_id} not found"})

    card = ctx.cards.get(card_id.upper())
    if card is None:
        return JSONResponse(
            status_code=404,
            content={"detail": f"card {card_id} not found in run {run_id}"},
        )

    return card.model_dump()


# ---------------------------------------------------------------------------
# GET /api/analyze/status/{run_id}
# ---------------------------------------------------------------------------

@router.get("/analyze/status/{run_id}")
async def run_status(run_id: str):
    ctx = get_run(run_id)
    if ctx is None:
        return JSONResponse(status_code=404, content={"detail": "run not found"})
    return {
        "run_id": ctx.run_id,
        "ticker": ctx.ticker,
        "as_of": ctx.as_of,
        "cards_done": list(ctx.cards.keys()),
        "has_aggregate": ctx.aggregate is not None,
        "has_verdict": ctx.verdict is not None,
        "elapsed_ms": ctx.elapsed_ms(),
    }


# ---------------------------------------------------------------------------
# POST /api/baseline — plain LLM comparison (no card context)
# ---------------------------------------------------------------------------

class BaselineRequest(BaseModel):
    query: str


@router.post("/baseline")
async def baseline(req: BaselineRequest):
    """Plain LLM response with no card context — for the stretch comparison toggle."""
    from app.llm.baseline import get_baseline_response
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_baseline_response, req.query)
    return result


class SimulationRequest(BaseModel):
    run_id: str
    usd_pct: float = Field(default=0, ge=-20, le=20)
    oil_pct: float = Field(default=0, ge=-20, le=20)
    yield_bp: float = Field(default=0, ge=-100, le=100)
    vix_pct: float = Field(default=0, ge=-30, le=30)


@router.post("/simulate")
async def simulate_run(req: SimulationRequest):
    ctx = get_run(req.run_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="run not found")
    if ctx.aggregate is None:
        raise HTTPException(status_code=409, detail="analysis has no aggregate result")

    cards = list(ctx.cards.values())
    base = aggregate_from_cards(cards)
    scenario = simulate(
        cards,
        SimulationOverrides(
            usd_pct=req.usd_pct,
            oil_pct=req.oil_pct,
            yield_bp=req.yield_bp,
            vix_pct=req.vix_pct,
        ),
    )
    baseline = {
        "composite_signal": base.composite_signal,
        "evidence_strength": base.evidence_strength,
        "coverage": base.coverage,
        "scenario_names": base.scenario_names,
        "scenario_scores": base.scenario_scores,
    }
    return {
        "run_id": req.run_id,
        "baseline": baseline,
        "scenario": scenario,
        "presentation": build_presentation(scenario, baseline),
        "composite_change": round(scenario["composite_signal"] - base.composite_signal, 6),
        "scenario_score_changes": [
            round(scenario["scenario_scores"][i] - base.scenario_scores[i], 6)
            for i in range(len(base.scenario_names))
        ],
        "disclaimer": "Illustrative sensitivity analysis, not a forecast or investment advice.",
    }


@router.post("/simulate/explain")
async def explain_simulation(req: SimulationRequest):
    ctx = get_run(req.run_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="run not found")
    if ctx.aggregate is None:
        raise HTTPException(status_code=409, detail="analysis has no aggregate result")

    import json
    from app.core.cache import TTL_EXPLANATION, cache_get, cache_key, cache_set
    from app.core.config import get_settings

    overrides = {
        "usd_pct": req.usd_pct,
        "oil_pct": req.oil_pct,
        "yield_bp": req.yield_bp,
        "vix_pct": req.vix_pct,
    }
    key = cache_key(
        "scenario_explanation",
        req.run_id,
        json.dumps(overrides, sort_keys=True, separators=(",", ":")),
    )
    cached = cache_get(key)
    if cached is not None:
        return {**cached, "cached": True}

    matching_card_ids = {
        "usd_pct": "C1",
        "yield_bp": "C2",
        "oil_pct": "C3",
        "vix_pct": "C4",
    }
    source_rows = []
    seen_urls: set[str] = set()
    for factor, value in overrides.items():
        if value == 0:
            continue
        card = ctx.cards.get(matching_card_ids[factor])
        if card is None:
            continue
        for source in card.sources:
            if source.url and source.url not in seen_urls:
                seen_urls.add(source.url)
                source_rows.append({
                    "number": len(source_rows) + 1,
                    "title": source.name,
                    "url": source.url,
                })

    active_factors = [
        name for factor, name in (
            ("usd_pct", "the US dollar"),
            ("oil_pct", "oil prices"),
            ("yield_bp", "10-year interest rates"),
            ("vix_pct", "market volatility"),
        ) if overrides[factor] != 0
    ]
    if active_factors:
        factor_text = ", ".join(active_factors)
        template = (
            f"This scenario changes {factor_text}. The model adjusts the matching evidence "
            "sources and recomputes the overall balance; it does not predict an actual market move. "
            "The result is illustrative and should be read alongside the cited source data."
        )
    else:
        template = (
            "This is the unchanged baseline scenario. It summarizes the current evidence without "
            "adding a hypothetical change, and it is not a forecast."
        )

    cards = list(ctx.cards.values())
    base_agg = aggregate_from_cards(cards)
    sim_res = simulate(cards, SimulationOverrides(**overrides))

    comparison_details = {
        "ticker": ctx.ticker,
        "query": ctx.query,
        "active_overrides": {
            k: (f"{v:+g}%" if "pct" in k else f"{v:+g} bp")
            for k, v in overrides.items() if v != 0
        },
        "baseline": {
            "composite_signal": round(base_agg.composite_signal, 3),
            "tailwind_confidence": f"{round(base_agg.scenario_scores[0] * 100, 1)}%",
            "mixed_confidence": f"{round(base_agg.scenario_scores[1] * 100, 1)}%",
            "headwind_confidence": f"{round(base_agg.scenario_scores[2] * 100, 1)}%",
        },
        "simulated": {
            "composite_signal": round(sim_res["composite_signal"], 3),
            "tailwind_confidence": f"{round(sim_res['scenario_scores'][0] * 100, 1)}%",
            "mixed_confidence": f"{round(sim_res['scenario_scores'][1] * 100, 1)}%",
            "headwind_confidence": f"{round(sim_res['scenario_scores'][2] * 100, 1)}%",
            "composite_shift": f"{round(sim_res['composite_signal'] - base_agg.composite_signal, 3):+g}",
        },
        "factor_impacts": sim_res.get("factor_impacts", []),
        "sources": source_rows,
    }

    cfg = get_settings()
    explanation = template
    used_llm = False
    can_call_llm = bool(cfg.llm_api_key) and not ctx.run_id.startswith("fixture-explanation-no-network")

    if can_call_llm:
        import re
        from app.llm.client import LLMError, chat_completion

        system_prompt = (
            "You are a senior equity research analyst specializing in financial sensitivity and scenario analysis. "
            "Write a concise, insightful analytical summary (3 to 4 sentences) comparing the simulated what-if sensitivity scenario "
            "against the baseline outlook for the company.\n"
            "Requirements:\n"
            "1. Explain the hypothetical macro shock applied and how it transmits to the company's fundamentals.\n"
            "2. Compare the simulated scenario outputs against the baseline (contrast composite signal and scenario probabilities).\n"
            "3. Conclude with the overall shift in evidence without predicting future stock prices or providing investment advice.\n"
            "4. If sources are provided, cite them inline using [number] notation (e.g. [1])."
        )
        user_prompt = json.dumps(comparison_details, separators=(",", ":"))

        try:
            candidate = chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens_override=450,
            )

            # Ensure primary source citation [1] is attached if model omitted it but sources exist
            if source_rows and not re.search(r"\[\d+\]", candidate):
                candidate = candidate.rstrip() + f" [{source_rows[0]['number']}]."

            if _valid_cited_explanation(
                candidate,
                len(source_rows),
                require_citation=bool(source_rows),
            ):
                explanation = candidate
                used_llm = True
            else:
                citations = [int(v) for v in re.findall(r"\[(\d+)\]", candidate)]
                if all(1 <= num <= len(source_rows) for num in citations):
                    explanation = candidate
                    used_llm = True
                else:
                    import logging
                    logging.getLogger("eventlens.explain").warning(
                        "Scenario explanation for run %s had invalid citations; falling back to template",
                        req.run_id,
                    )
        except LLMError as exc:
            import logging
            logging.getLogger("eventlens.explain").warning("LLM explanation call failed: %s", exc)

    result = {
        "explanation": explanation,
        "citations": source_rows,
        "comparison": comparison_details,
        "cached": False,
        "used_llm": used_llm,
    }
    cache_set(key, result, TTL_EXPLANATION)
    return result


@router.get("/precedents")
async def precedents(
    ticker: str,
    event_type: str,
    as_of: date,
    market_mood: str = "mixed",
):
    matches = find_precedents(
        ticker=ticker,
        event_type=event_type,
        as_of=as_of.isoformat(),
        market_mood=market_mood,
    )
    from app.precedents.engine import compute_cohort_stats, synthesize_precedents
    cohort = compute_cohort_stats(matches) if matches else None
    ai_synthesis = (
        synthesize_precedents(ticker, event_type, as_of.isoformat(), matches, cohort)
        if matches and cohort
        else None
    )
    return {
        "matches": matches,
        "cohort": cohort,
        "ai_synthesis": ai_synthesis,
        "note": (
            "Matches are drawn from the verified local precedent library."
            if matches
            else "No verified precedent dataset is installed. Build it with backend/scripts/build_precedents.py."
        ),
    }


def _unusual_days(card) -> list[dict[str, Any]]:
    if card.id != "C5":
        return []
    points = sorted(
        (point for point in card.series if point.v is not None),
        key=lambda point: point.t,
    )
    deltas = []
    for previous, current in zip(points, points[1:]):
        previous_price = float(previous.v)
        current_price = float(current.v)
        if previous_price <= 0 or current_price <= 0:
            continue
        move = (current_price / previous_price - 1) * 100
        deltas.append({
            "date": current.t,
            "adjusted_price": current_price,
            "daily_percentage_move": move,
        })
    if len(deltas) < 10:
        return []

    center = median(item["daily_percentage_move"] for item in deltas)
    deviations = [abs(item["daily_percentage_move"] - center) for item in deltas]
    mad = median(deviations)
    if mad > 0:
        for item in deltas:
            item["robust_score"] = 0.6745 * (item["daily_percentage_move"] - center) / mad
    else:
        for item in deltas:
            deviation = item["daily_percentage_move"] - center
            item["robust_score"] = 10.0 if deviation > 0 else -10.0 if deviation < 0 else 0.0

    unusual = [item for item in deltas if abs(item["robust_score"]) >= 3.5]
    unusual.sort(key=lambda item: (-abs(item["robust_score"]), item["date"]))
    return [
        {**item, "robust_score": round(item["robust_score"], 2)}
        for item in unusual[:5]
    ]


@router.get("/cards/{card_id}/unusual-days")
async def unusual_days(card_id: str, run_id: str = Query(default="")):
    if not run_id:
        raise HTTPException(status_code=400, detail="run_id is required")
    ctx = get_run(run_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    card = ctx.cards.get(card_id.upper())
    if card is None or card.status != "done":
        raise HTTPException(status_code=404, detail=f"card {card_id} not found in run {run_id}")
    days = _unusual_days(card)
    if ctx.is_fixture:
        fixture_days = ctx.event_evidence.get("markers", {}).get(card.id, [])
        by_date = {item["date"]: item for item in days}
        for marker in fixture_days:
            by_date[marker["date"]] = marker
        days = sorted(
            by_date.values(),
            key=lambda item: -abs(item["robust_score"]),
        )[:5]
    return {"card_id": card.id, "days": days}


class ExplainDayRequest(BaseModel):
    run_id: str
    card_id: str
    event_date: date


@router.post("/explain-day")
async def explain_day(req: ExplainDayRequest):
    ctx = get_run(req.run_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="run not found")
    card = ctx.cards.get(req.card_id.upper())
    if card is None or card.status != "done":
        raise HTTPException(status_code=404, detail="card not found in run")

    event_date = req.event_date.isoformat()
    from app.core.cache import TTL_EXPLANATION, cache_get, cache_key, cache_set
    cache_id = cache_key("day_explanation", req.run_id, card.id, event_date)
    cached = cache_get(cache_id)
    if cached is not None:
        return {**cached, "cached": True}

    unusual = _unusual_days(card)
    if ctx.is_fixture:
        unusual += ctx.event_evidence.get("markers", {}).get(card.id, [])
    event = next((item for item in unusual if item["date"] == event_date), None)
    if event is None:
        raise HTTPException(status_code=400, detail="date is not marked unusual for this card")

    if ctx.is_fixture:
        curated = ctx.event_evidence.get("explanations", {}).get(event_date)
        if curated:
            result = {
                **curated,
                "cached": False,
                "used_llm": False,
            }
            cache_set(cache_id, result, TTL_EXPLANATION)
            return result

    related = card.related_series

    def daily_move(name: str) -> float | None:
        series = related.get(name, [])
        selected = next((idx for idx, point in enumerate(series) if point.t == event_date), None)
        if selected is None or selected == 0 or series[selected - 1].v in (None, 0) or series[selected].v is None:
            return None
        return (float(series[selected].v) / float(series[selected - 1].v) - 1) * 100

    stock_move = event["daily_percentage_move"]
    sector_move = daily_move("sector")
    market_move = daily_move("market")
    classification = _classify_move(stock_move, sector_move, market_move)

    citations: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    def add_citation(title: str, url: str, source_date: str | None = None, kind: str = "source") -> None:
        if url.startswith("https://") and url not in seen_urls:
            seen_urls.add(url)
            citations.append({
                "number": len(citations) + 1,
                "title": title,
                "url": url,
                "date": source_date,
                "type": kind,
            })

    for source in card.sources:
        add_citation(source.name, source.url, kind="price_data")

    macro_observations: dict[str, dict[str, Any]] = {}
    for related_card_id in ("C2", "C3"):
        related_card = ctx.cards.get(related_card_id)
        if related_card is None:
            continue
        observation = _same_day_observation(related_card, event_date)
        if observation is None:
            continue
        observation["source_numbers"] = []
        for source in related_card.sources:
            before_count = len(citations)
            add_citation(source.name, source.url, kind="macro_data")
            if len(citations) > before_count:
                observation["source_numbers"].append(citations[-1]["number"])
        macro_observations[related_card_id] = observation

    filings: list[dict[str, Any]] = []
    headlines: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {
        "query": ctx.query,
        "ticker": ctx.ticker,
        "date": event_date,
        "adjusted_price": event["adjusted_price"],
        "daily_percentage_move": stock_move,
        "sector_daily_move": sector_move,
        "market_daily_move": market_move,
        "classification": classification,
        "same_day_oil_and_rates": macro_observations,
    }

    if not ctx.is_fixture:
        from app.core.edgar_client import get_filings_near_date
        from app.core.finnhub_client import company_news

        try:
            filings = get_filings_near_date(ctx.ticker, event_date)
        except Exception as exc:
            filings = []
            import logging
            logging.getLogger("eventlens.explain").warning("SEC filing lookup failed: %s", exc)
        for filing in filings:
            add_citation(filing["title"], filing["url"], filing["date"], "sec_filing")

        headlines = company_news(ctx.ticker, event_date)
        for headline in headlines:
            published = datetime.fromtimestamp(headline["datetime"], tz=timezone.utc).date().isoformat()
            add_citation(headline["title"], headline["url"], published, "company_news")
    evidence["filings"] = filings
    evidence["headlines"] = headlines

    template = _day_explanation_template(
        ctx.ticker,
        event_date,
        stock_move,
        sector_move,
        market_move,
        classification,
        citations,
        macro_observations,
        filings,
        headlines,
    )
    explanation = template
    used_llm = False
    from app.core.config import get_settings
    cfg = get_settings()
    if not ctx.is_fixture and cfg.llm_api_key:
        import json
        from app.llm.client import LLMError, chat_completion

        try:
            candidate = chat_completion(
                system_prompt=(
                    "Write three or four concise sentences explaining the selected daily stock move. "
                    "Use only the supplied evidence; do not infer causation. Include numbered citations "
                    "for factual claims, using only the supplied citation numbers. Do not give investment advice."
                ),
                user_prompt=json.dumps(
                    {"evidence": evidence, "citations": citations},
                    separators=(",", ":"),
                ),
                max_tokens_override=350,
            )
            if _valid_cited_explanation(candidate, len(citations)):
                explanation = candidate
                used_llm = True
            else:
                import logging
                logging.getLogger("eventlens.explain").warning(
                    "LLM explanation for %s on %s failed sentence/citation validation",
                    ctx.ticker,
                    req.event_date,
                )
        except LLMError as exc:
            import logging
            logging.getLogger("eventlens.explain").warning("LLM explanation unavailable: %s", exc)

    result = {
        "explanation": explanation,
        "classification": classification,
        "citations": citations,
        "cached": False,
        "used_llm": used_llm,
    }
    cache_set(cache_id, result, TTL_EXPLANATION)
    return result


def _classify_move(
    stock: float,
    sector: float | None,
    market: float | None,
) -> str:
    if sector is None or market is None:
        return "insufficient_evidence"
    company_gap = abs(stock - sector)
    sector_gap = abs(sector - market)
    if company_gap >= max(sector_gap, 0.25):
        return "company_led"
    if sector_gap >= 0.25:
        return "sector_led"
    return "market_led"


def _same_day_observation(card, event_date: str) -> dict[str, Any] | None:
    points = sorted(
        (point for point in card.series if point.v is not None),
        key=lambda point: point.t,
    )
    index = next((i for i, point in enumerate(points) if point.t == event_date), None)
    if index is None or index == 0:
        return None

    value = float(points[index].v)
    previous = float(points[index - 1].v)
    if card.id == "C2":
        return {
            "name": "10-year rate",
            "value": value,
            "change": round((value - previous) * 100, 2),
            "unit": "basis points",
        }
    if previous <= 0 or value <= 0:
        return None
    return {
        "name": "oil price",
        "value": value,
        "change": round((value / previous - 1) * 100, 2),
        "unit": "%",
    }


def _day_explanation_template(
    ticker: str,
    event_date: str,
    stock: float,
    sector: float | None,
    market: float | None,
    classification: str,
    citations: list[dict[str, Any]],
    macro_observations: dict[str, dict[str, Any]],
    filings: list[dict[str, Any]],
    headlines: list[dict[str, Any]],
) -> str:
    def citation(number: int) -> str:
        return f" [{number}]" if len(citations) >= number else ""

    first = (
        f"{ticker}'s adjusted closing price moved {stock:+.2f}% on {event_date}."
        f"{citation(1)}"
    )
    if sector is not None and market is not None:
        second = (
            f"The sector benchmark moved {sector:+.2f}%{citation(2)}, while the broad market moved "
            f"{market:+.2f}%{citation(3)} that day."
        )
    else:
        second = "A complete same-day sector and broad-market comparison was not available."
    second = second.rstrip(".")
    for card_id, label in (("C3", "Oil prices"), ("C2", "10-year rates")):
        observation = macro_observations.get(card_id)
        if observation is None:
            continue
        source_numbers = observation["source_numbers"]
        refs = "".join(citation(number) for number in source_numbers[:1])
        change = observation["change"]
        if card_id == "C2":
            second += f"; {label.lower()} changed {change:+.2f} basis points{refs}"
        else:
            second += f"; {label.lower()} moved {change:+.2f}% on the day{refs}"
    second += "."
    label = classification.replace("_", " ")
    event_sources = []
    for source in filings[:1]:
        number = next((item["number"] for item in citations if item["url"] == source["url"]), None)
        if number is not None:
            event_sources.append(f"a nearby SEC filing was dated {source['date']}{citation(number)}")
    for headline in headlines[:1]:
        number = next((item["number"] for item in citations if item["url"] == headline["url"]), None)
        if number is not None:
            published = datetime.fromtimestamp(headline["datetime"], tz=timezone.utc).date().isoformat()
            event_sources.append(f"a company-news headline was dated {published}{citation(number)}")
    third = (
        f"Collected event evidence shows {'; '.join(event_sources)}."
        if event_sources
        else "No nearby SEC filing or dated company-news headline was available in the collected evidence."
    )
    fourth = (
        f"Relative to those benchmarks, the move is classified as {label}; this comparison does not "
        "prove what caused the price change."
    )
    return " ".join((first, second, third, fourth))


def _valid_cited_explanation(
    text: str,
    citation_count: int,
    require_citation: bool = True,
) -> bool:
    import re

    sentences = [sentence for sentence in re.split(r"(?<=[.!?])\s+", text.strip()) if sentence]
    citations = [int(value) for value in re.findall(r"\[(\d+)\]", text)]
    return (
        3 <= len(sentences) <= 4
        and (bool(citations) or not require_citation)
        and all(1 <= number <= citation_count for number in citations)
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Simple keyword→ticker map for the scripted demos when ticker is not sent
_TICKER_HINTS: list[tuple[list[str], str]] = [
    (["intel", "intc"],           "INTC"),
    (["nvidia", "nvda"],          "NVDA"),
    (["exxon", "xom"],            "XOM"),
    (["jpmorgan", "jpm", "jp morgan"], "JPM"),
    (["apple", "aapl"],           "AAPL"),
    (["microsoft", "msft"],       "MSFT"),
    (["amazon", "amzn"],          "AMZN"),
    (["starbucks", "sbux"],       "SBUX"),
    (["disney", "dis"],           "DIS"),
    (["boeing", "ba"],            "BA"),
    (["raytheon", "rtx"],         "RTX"),
    (["chevron", "cvx"],          "CVX"),
    (["schwab", "schw"],          "SCHW"),
    (["unitedhealth", "unh"],     "UNH"),
    (["gm", "general motors"],    "GM"),
]

def _extract_ticker_hint(query: str) -> str:
    q = query.lower()
    for keywords, ticker in _TICKER_HINTS:
        if any(kw in q for kw in keywords):
            return ticker
    return "UNKNOWN"
