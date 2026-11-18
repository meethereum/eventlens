"""
Query parsing — LLM call 1.

Sends the user's free-text query to the LLM and expects strict JSON:
  {ticker, event_type, as_of, horizon_days, intent}

If the LLM is unconfigured or fails, falls back to deterministic ticker
matching (already implemented in analyze.py) with default values.
"""
from __future__ import annotations

import logging
from datetime import date

from pydantic import BaseModel, Field

from app.llm.client import json_completion, LLMError
from app.core.config import get_settings

logger = logging.getLogger("eventlens.llm.parsing")


# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------

class ParsedQueryLLM(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol, uppercase")
    event_type: str = Field(..., description="Short description of the event")
    as_of: str = Field(default="", description="ISO date the analysis is as of")
    horizon_days: int = Field(default=20, ge=1, le=90)
    intent: str = Field(..., description="One of: analysis, advice_request, out_of_scope")


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a financial query parser. Given a user's question about a company event, extract structured metadata.

Return ONLY valid JSON with this exact schema:
{
  "ticker": "UPPERCASE_TICKER",
  "event_type": "short description of the event (e.g. 'CEO departure', 'earnings beat', 'rate decision')",
  "as_of": "ISO date string (YYYY-MM-DD), or empty string if not specified",
  "horizon_days": integer (default 20),
  "intent": "one of: analysis | advice_request | out_of_scope"
}

Rules:
- ticker must be a real US stock ticker (uppercase). If the user mentions "Intel" use INTC, "Nvidia" use NVDA, etc.
- intent is "analysis" if the user asks what to expect / what it means / impact analysis
- intent is "advice_request" if the user asks whether to buy, sell, hold, or for a price target
- intent is "out_of_scope" if the question is not about a specific company event
- If the user specifies a date context (e.g. "just ousted", "last week", a specific date), set as_of accordingly. Otherwise leave empty.
- Output ONLY the JSON object, no markdown, no explanation."""


# ---------------------------------------------------------------------------
# Covered tickers (for deterministic fallback)
# ---------------------------------------------------------------------------

COVERED_TICKERS = {
    "NVDA", "INTC", "AAPL", "MSFT", "GM", "SBUX", "AMZN",
    "DIS", "BA", "RTX", "XOM", "CVX", "JPM", "SCHW", "UNH",
}

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

_ADVICE_PATTERNS = [
    "should i buy", "should i sell", "should i hold", "should i invest",
    "buy or sell", "is it a good time to buy", "price target",
    "will the stock go up", "will the stock go down",
]


def _deterministic_ticker(query: str) -> str:
    q = query.lower()
    for keywords, ticker in _TICKER_HINTS:
        if any(kw in q for kw in keywords):
            return ticker
    return "UNKNOWN"


def _deterministic_intent(query: str) -> str:
    q = query.lower()
    if any(p in q for p in _ADVICE_PATTERNS):
        return "advice_request"
    return "analysis"


def _deterministic_event_type(query: str) -> str:
    """Extract a rough event type from the query."""
    q = query.lower()
    if "ceo" in q and ("oust" in q or "fire" in q or "resign" in q or "depart" in q):
        return "CEO departure"
    if "earnings" in q or "beat" in q or "miss" in q:
        return "earnings event"
    if "oil" in q or "crude" in q or "energy" in q:
        return "commodity shock"
    if "bank" in q and ("collaps" in q or "fail" in q):
        return "banking crisis"
    if "fed" in q and ("rate" in q or "hike" in q or "cut" in q):
        return "Fed rate decision"
    if "invasion" in q or "war" in q or "geopolit" in q:
        return "geopolitical shock"
    if "deepseek" in q or "ai" in q:
        return "AI competitive shock"
    return "company event"


# ---------------------------------------------------------------------------
# Parse query
# ---------------------------------------------------------------------------

def parse_query(query: str, fallback_ticker: str = "", fallback_as_of: str = "") -> dict:
    """
    Parse the user's query using LLM call 1.
    Returns a dict with: ticker, event_type, as_of, horizon_days, intent,
    latency_ms, used_llm (bool), used_fallback_model (bool).

    If LLM is unconfigured or fails, uses deterministic fallback.
    """
    import time
    t0 = time.time()

    cfg = get_settings()

    if not cfg.llm_api_key:
        # Deterministic fallback
        ticker = fallback_ticker.upper() or _deterministic_ticker(query)
        return {
            "ticker": ticker,
            "event_type": _deterministic_event_type(query),
            "as_of": fallback_as_of or date.today().isoformat(),
            "horizon_days": 20,
            "intent": _deterministic_intent(query),
            "latency_ms": 5,
            "used_llm": False,
            "used_fallback_model": False,
        }

    user_prompt = f"User query: {query}\n\nExtract the metadata as JSON."

    parsed, raw, used_fallback = json_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_model=ParsedQueryLLM,
    )

    latency_ms = int((time.time() - t0) * 1000)

    if parsed is None:
        logger.warning("LLM parsing failed, using deterministic fallback: %s", str(raw)[:100])
        ticker = fallback_ticker.upper() or _deterministic_ticker(query)
        return {
            "ticker": ticker,
            "event_type": _deterministic_event_type(query),
            "as_of": fallback_as_of or date.today().isoformat(),
            "horizon_days": 20,
            "intent": _deterministic_intent(query),
            "latency_ms": latency_ms,
            "used_llm": False,
            "used_fallback_model": False,
        }

    return {
        "ticker": parsed.ticker.upper(),
        "event_type": parsed.event_type,
        "as_of": parsed.as_of or fallback_as_of or date.today().isoformat(),
        "horizon_days": parsed.horizon_days,
        "intent": parsed.intent,
        "latency_ms": latency_ms,
        "used_llm": True,
        "used_fallback_model": used_fallback,
    }
