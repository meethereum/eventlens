from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from app.precedents.schema import PrecedentRecord

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "precedents.json"

SECTORS = {
    "NVDA": "technology", "INTC": "technology", "AAPL": "technology",
    "MSFT": "technology", "GM": "consumer", "SBUX": "consumer",
    "AMZN": "consumer", "DIS": "communication", "BA": "industrials",
    "RTX": "industrials", "XOM": "energy", "CVX": "energy",
    "JPM": "financials", "SCHW": "financials", "UNH": "healthcare",
}

_EVENT_TAGS = {
    "leadership": ("ceo", "chief executive", "leadership", "oust", "resign", "departure"),
    "earnings": ("earnings", "revenue", "profit", "guidance", "beat", "miss"),
    "geopolitical": ("war", "invasion", "geopolitical", "sanction", "oil shock"),
    "banking": ("bank", "svb", "deposit", "contagion", "liquidity"),
    "technology": ("ai", "deepseek", "chip", "semiconductor", "technology"),
    "regulatory": ("regulation", "antitrust", "lawsuit", "regulatory"),
    "operational": ("outage", "recall", "strike", "safety", "cyberattack"),
}

_SECTOR_ALIASES = {
    "consumer discretionary": "consumer",
    "communication services": "communication",
    "health care": "healthcare",
}


def event_category(event_type: str) -> str:
    text = event_type.lower()
    for category, terms in _EVENT_TAGS.items():
        if any(term in text for term in terms):
            return category
    return "company_event"


def find_precedents(
    ticker: str,
    event_type: str,
    as_of: str,
    market_mood: str = "mixed",
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Rank the locally curated analogs without using events on/after as_of."""
    cutoff = date.fromisoformat(as_of)
    target_ticker = ticker.upper()
    target_sector = _SECTOR_ALIASES.get(SECTORS.get(target_ticker, "").lower(), SECTORS.get(target_ticker, "unknown"))
    target_category = event_category(event_type)
    rows = [
        PrecedentRecord.model_validate(row).model_dump(mode="json")
        for row in json.loads(DATA_PATH.read_text(encoding="utf-8"))
    ]
    ranked: list[dict[str, Any]] = []

    for row in rows:
        completed_on = max(
            date.fromisoformat(row["outcomes"]["series"][entity][-1]["date"])
            for entity in ("stock", "sector", "spy")
        )
        if completed_on >= cutoff:
            continue

        score = 0.0
        reasons: list[str] = []
        if row["ticker"].upper() == target_ticker:
            score += 0.4
            reasons.append("same company")
        if row["category"] == target_category:
            score += 0.4
            reasons.append("similar event type")
        row_sector = _SECTOR_ALIASES.get(row["sector"].lower(), row["sector"].lower())
        if target_sector != "unknown" and row_sector == target_sector:
            score += 0.15
            reasons.append("same sector")
        if row["market_mood"] == market_mood:
            score += 0.05
            reasons.append("similar market backdrop")

        if score == 0:
            continue
        ranked.append({
            **row,
            "similarity": round(score, 2),
            "match_reason": "; ".join(reason.capitalize() for reason in reasons) + ".",
            "days_before_as_of": (cutoff - date.fromisoformat(row["event_date"])).days,
        })

    ranked.sort(
        key=lambda item: (
            -item["similarity"],
            -date.fromisoformat(item["event_date"]).toordinal(),
            item["id"],
        )
    )
    return ranked[:max(0, limit)]


def compute_cohort_stats(matches: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate statistical KPI benchmarks and a 60-day trajectory corridor."""
    import numpy as np

    if not matches:
        return {}

    stock_d5 = [float(m["outcomes"]["returns"]["stock"]["d5"]) for m in matches]
    stock_d20 = [float(m["outcomes"]["returns"]["stock"]["d20"]) for m in matches]
    stock_d60 = [float(m["outcomes"]["returns"]["stock"]["d60"]) for m in matches]

    sector_d5 = [float(m["outcomes"]["returns"]["sector"]["d5"]) for m in matches]
    sector_d20 = [float(m["outcomes"]["returns"]["sector"]["d20"]) for m in matches]
    sector_d60 = [float(m["outcomes"]["returns"]["sector"]["d60"]) for m in matches]

    alpha_d5 = [s - sec for s, sec in zip(stock_d5, sector_d5)]
    alpha_d20 = [s - sec for s, sec in zip(stock_d20, sector_d20)]
    alpha_d60 = [s - sec for s, sec in zip(stock_d60, sector_d60)]

    win_rate_20 = sum(1 for x in stock_d20 if x > 0) / len(stock_d20) * 100
    win_rate_60 = sum(1 for x in stock_d60 if x > 0) / len(stock_d60) * 100
    alpha_win_rate_20 = sum(1 for a in alpha_d20 if a > 0) / len(alpha_d20) * 100

    corridor = []
    # Build 60-day day-by-day corridor
    max_days = min(61, min(len(m["outcomes"]["series"]["stock"]) for m in matches))
    for day in range(max_days):
        day_stock = [float(m["outcomes"]["series"]["stock"][day]["value"]) for m in matches]
        day_sector = [float(m["outcomes"]["series"]["sector"][day]["value"]) for m in matches]
        day_spy = [float(m["outcomes"]["series"]["spy"][day]["value"]) for m in matches]

        alphas_sec = [s - sec for s, sec in zip(day_stock, day_sector)]
        alphas_spy = [s - spy for s, spy in zip(day_stock, day_spy)]

        corridor.append({
            "day": day,
            "median": round(float(np.median(day_stock)), 2),
            "q1": round(float(np.percentile(day_stock, 25)), 2),
            "q3": round(float(np.percentile(day_stock, 75)), 2),
            "alpha_sector": round(float(np.median(alphas_sec)), 2),
            "alpha_spy": round(float(np.median(alphas_spy)), 2),
        })

    return {
        "cases_count": len(matches),
        "median_stock_d5": round(float(np.median(stock_d5)), 2),
        "median_stock_d20": round(float(np.median(stock_d20)), 2),
        "median_stock_d60": round(float(np.median(stock_d60)), 2),
        "median_sector_d20": round(float(np.median(sector_d20)), 2),
        "median_alpha_d5": round(float(np.median(alpha_d5)), 2),
        "median_alpha_d20": round(float(np.median(alpha_d20)), 2),
        "median_alpha_d60": round(float(np.median(alpha_d60)), 2),
        "win_rate_20": round(win_rate_20, 1),
        "win_rate_60": round(win_rate_60, 1),
        "alpha_win_rate_20": round(alpha_win_rate_20, 1),
        "corridor": corridor,
    }


def synthesize_precedents(
    ticker: str,
    event_type: str,
    as_of: str,
    matches: list[dict[str, Any]],
    cohort: dict[str, Any],
) -> dict[str, Any]:
    """Generate an institutional AI synthesis of the precedent cohort."""
    if not matches or not cohort:
        return {"summary": "", "used_llm": False, "cached": False}

    from app.core.cache import TTL_EXPLANATION, cache_get, cache_key, cache_set
    from app.core.config import get_settings

    key = cache_key("precedent_synthesis", ticker.upper(), event_type.lower(), as_of)
    cached = cache_get(key)
    if cached is not None:
        return {**cached, "cached": True}

    med_20 = cohort["median_stock_d20"]
    med_60 = cohort["median_stock_d60"]
    alpha_20 = cohort["median_alpha_d20"]
    win_rate = cohort["win_rate_60"]

    direction_20 = "gained" if med_20 > 0 else "declined"
    alpha_dir = "outperformed" if alpha_20 > 0 else "underperformed"
    template_summary = (
        f"Across {cohort['cases_count']} historical precedents for {ticker}, stocks {direction_20} by a median of {med_20:+.1f}% over the initial 20 trading days and {med_60:+.1f}% by day 60. "
        f"Relative to sector benchmarks, the cohort {alpha_dir} by a median alpha spread of {alpha_20:+.1f}%, with {win_rate:.0f}% of cases recording positive absolute returns at 60 days. "
        f"These patterns reflect how initial post-event volatility resolved historically without predicting future returns."
    )

    cfg = get_settings()
    summary = template_summary
    used_llm = False

    if cfg.llm_api_key and not getattr(cfg, "is_demo_mode", False):
        from app.llm.client import LLMError, chat_completion

        top_cases = [
            {
                "ticker": m["ticker"],
                "event_date": m["event_date"],
                "stock_20d": f"{m['outcomes']['returns']['stock']['d20']:+.1f}%",
                "sector_20d": f"{m['outcomes']['returns']['sector']['d20']:+.1f}%",
                "summary": m["summary"],
            }
            for m in matches[:3]
        ]
        cohort_metrics = {
            "total_precedents_analyzed": cohort["cases_count"],
            "median_stock_return_5d": f"{cohort['median_stock_d5']:+.1f}%",
            "median_stock_return_20d": f"{cohort['median_stock_d20']:+.1f}%",
            "median_stock_return_60d": f"{cohort['median_stock_d60']:+.1f}%",
            "median_alpha_vs_sector_20d": f"{cohort['median_alpha_d20']:+.1f}%",
            "positive_60d_win_rate": f"{cohort['win_rate_60']:.0f}%",
        }

        system_prompt = (
            "You are a senior equity research analyst. Analyze and synthesize these historical precedent cases "
            "for this corporate event into a concise, high-value 3-sentence analytical briefing.\n"
            "1. Summarize the historical trajectory across 5d, 20d, and 60d trading windows (initial reaction vs drift).\n"
            "2. Contrast the stock performance relative to its sector ETF (identifying whether company-specific alpha or broader sector beta dominated).\n"
            "3. State the core historical takeaway and what differentiated the stronger outcomes from weaker ones, avoiding price predictions or investment advice."
        )
        user_prompt = json.dumps(
            {"ticker": ticker, "event_type": event_type, "cohort": cohort_metrics, "cases": top_cases},
            separators=(",", ":"),
        )

        try:
            candidate = chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens_override=800,
            )
            if candidate and len(candidate.strip()) > 50:
                summary = candidate.strip()
                used_llm = True
        except LLMError as exc:
            import logging
            logging.getLogger("eventlens.precedents").warning("LLM precedent synthesis failed: %s", exc)

    result = {
        "summary": summary,
        "used_llm": used_llm,
        "cached": False,
    }
    cache_set(key, result, TTL_EXPLANATION)
    return result
