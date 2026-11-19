"""Optional, cached Finnhub company-news lookups for event explanations."""
from __future__ import annotations

import logging
import threading
import time
from datetime import date, timedelta
from typing import Any

import httpx

from app.core.cache import TTL_NEWS, cache_get, cache_key, cache_set
from app.core.config import get_settings

logger = logging.getLogger("eventlens.finnhub")

_RATE_LOCK = threading.Lock()
_LAST_REQUEST = 0.0
_MIN_INTERVAL_S = 1.0


def company_news(ticker: str, event_date: str, lookback_days: int = 2) -> list[dict[str, Any]]:
    cfg = get_settings()
    if not cfg.finnhub_api_key:
        return []

    date.fromisoformat(event_date)
    start = (date.fromisoformat(event_date) - timedelta(days=lookback_days)).isoformat()
    end = (date.fromisoformat(event_date) + timedelta(days=1)).isoformat()
    key = cache_key("finnhub_news", ticker.upper(), start, end)
    cached = cache_get(key)
    if cached is not None:
        return cached

    global _LAST_REQUEST
    with _RATE_LOCK:
        wait_s = _MIN_INTERVAL_S - (time.monotonic() - _LAST_REQUEST)
        if wait_s > 0:
            time.sleep(wait_s)
        _LAST_REQUEST = time.monotonic()

    try:
        response = httpx.get(
            "https://finnhub.io/api/v1/company-news",
            params={
                "symbol": ticker.upper(),
                "from": start,
                "to": end,
                "token": cfg.finnhub_api_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("Finnhub returned an unexpected company-news payload")
        items = [
            {
                "title": item["headline"].strip(),
                "url": item["url"],
                "source": item.get("source", "Finnhub"),
                "datetime": int(item["datetime"]),
                "summary": item.get("summary", ""),
            }
            for item in payload
            if isinstance(item, dict)
            and isinstance(item.get("headline"), str)
            and item.get("headline", "").strip()
            and isinstance(item.get("url"), str)
            and item["url"].startswith("https://")
            and isinstance(item.get("datetime"), (int, float))
        ][:8]
        cache_set(key, items, TTL_NEWS)
        return items
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.warning("Finnhub news unavailable for %s: %s", ticker, exc)
        cache_set(key, [], TTL_NEWS)
        return []
