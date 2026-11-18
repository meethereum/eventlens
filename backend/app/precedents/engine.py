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
