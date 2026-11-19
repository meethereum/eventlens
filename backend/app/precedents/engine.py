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

_COMPANY_NAMES = {
    "NVDA": "Nvidia", "INTC": "Intel", "AAPL": "Apple", "MSFT": "Microsoft",
    "GM": "General Motors", "SBUX": "Starbucks", "AMZN": "Amazon",
    "DIS": "Disney", "BA": "Boeing", "RTX": "RTX Corporation",
    "XOM": "ExxonMobil", "CVX": "Chevron", "JPM": "JPMorgan Chase",
    "SCHW": "Charles Schwab", "UNH": "UnitedHealth",
}


def _company_name(ticker: str) -> str:
    return _COMPANY_NAMES.get(ticker.upper(), "the company")


def _company_names_in_text(text: str) -> str:
    import re

    for symbol in sorted(_COMPANY_NAMES, key=len, reverse=True):
        suffix = r"(?!\s+Corporation\b)" if symbol == "RTX" else ""
        text = re.sub(
            rf"\b{re.escape(symbol)}\b{suffix}",
            _COMPANY_NAMES[symbol],
            text,
            flags=re.IGNORECASE,
        )
    return text


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

    direction_20 = "went up" if med_20 > 0 else "fell"
    direction_60 = "positive" if med_60 > 0 else "negative"
    comp_direction = "better" if alpha_20 > 0 else "worse"
    template_summary = (
        f"Looking at {cohort['cases_count']} similar past events, stocks {direction_20} by about "
        f"{abs(med_20):.1f}% in the first month and ended {direction_60} after two months "
        f"(median: {med_60:+.1f}%). "
        f"Compared to other companies in the same industry, the affected stock did {comp_direction} "
        f"by roughly {abs(alpha_20):.1f} percentage points. "
        f"About {win_rate:.0f}% of similar cases saw the stock higher after two months. "
        f"These are observations from past events — they describe patterns, not predictions."
    )

    cfg = get_settings()
    summary = template_summary
    used_llm = False

    if cfg.llm_api_key and not getattr(cfg, "is_demo_mode", False):
        from app.llm.client import LLMError, chat_completion

        top_cases = [
            {
                "company": _company_name(m["ticker"]),
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
            "You are helping a trader understand what history tells us about a news event they are researching. "
            "You have data on similar past events — what happened, how the stock moved, and how it compared to the broader market. "
            "Write a useful 4-to-5 sentence summary in plain conversational English. No jargon, no ticker symbols, no financial terms a non-expert wouldn't know.\n\n"
            "Cover these four things:\n"
            "1. What the numbers show: how did stocks move in the first week, first month, and after two months? Use the actual numbers provided.\n"
            "2. Did the affected company do better or worse than the rest of its industry during this period — and by roughly how much?\n"
            "3. What separated the cases that bounced back from the ones that kept falling? Be specific — was it a quick CEO replacement, a government backstop, strong cash reserves, or something else?\n"
            "4. What is the one practical takeaway a trader should keep in mind given this event type?\n\n"
            "Rules:\n"
            "- Write in plain sentences. No bullet points.\n"
            "- Use company names, never ticker symbols.\n"
            "- Do not give investment advice or predict what will happen.\n"
            "- Do not use the words 'alpha', 'beta', 'cohort', 'trajectory', 'precedent', 'historical', or 'metric'.\n"
            "- If the data covers fewer than 3 cases, say so and note the limited sample.\n"
            "- Aim for around 120 words."
        )
        user_prompt = json.dumps(
            {
                "event_type": event_type,
                "cases_analyzed": cohort["cases_count"],
                "stock_move_5_days": f"{cohort['median_stock_d5']:+.1f}%",
                "stock_move_20_days": f"{cohort['median_stock_d20']:+.1f}%",
                "stock_move_60_days": f"{cohort['median_stock_d60']:+.1f}%",
                "vs_industry_20_days": f"{cohort['median_alpha_d20']:+.1f}%",
                "positive_outcome_rate_60d": f"{cohort['win_rate_60']:.0f}%",
                "example_cases": [
                    {
                        "company": _company_name(m["ticker"]),
                        "what_happened": m["summary"],
                        "stock_after_20_days": f"{m['outcomes']['returns']['stock']['d20']:+.1f}%",
                        "industry_after_20_days": f"{m['outcomes']['returns']['sector']['d20']:+.1f}%",
                    }
                    for m in matches[:4]
                ],
            },
            separators=(",", ":"),
        )

        try:
            candidate = chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens_override=600,
            )
            if candidate and len(candidate.strip()) > 50:
                summary = _company_names_in_text(candidate.strip())
                used_llm = True
        except LLMError as exc:
            import logging
            logging.getLogger("eventlens.precedents").warning("LLM precedent synthesis failed: %s", exc)

    result = {
        "summary": _company_names_in_text(summary),
        "used_llm": used_llm,
        "cached": False,
    }
    cache_set(key, result, TTL_EXPLANATION)
    return result
