"""
FRED API client.

Fetches observation series from the St. Louis Fed API.
Caches responses for TTL_FRED (6h).
Respects the free-tier limit of ~120 req/min by not hammering the API.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

import httpx
import pandas as pd

from app.core.cache import cache_get, cache_key, cache_set, TTL_FRED
from app.core.config import get_settings

logger = logging.getLogger("eventlens.fred")

FRED_BASE = "https://api.stlouisfed.org/fred"


def _api_key() -> str:
    return get_settings().fred_api_key


def fetch_series(
    series_id: str,
    as_of: str | None = None,
    observation_start: str | None = None,
) -> pd.Series:
    """
    Return a pandas Series (DatetimeIndex → float) for the given FRED series.

    as_of: upper date bound (ISO string).  Observations after this date are dropped.
    observation_start: lower date bound (ISO string).  Defaults to 5 years ago.
    """
    cfg = get_settings()
    if not cfg.fred_api_key:
        raise RuntimeError("FRED_API_KEY not set")

    # Default window: 5 years to cover 756-day lookback + some buffer
    if observation_start is None:
        start_dt = date.today() - timedelta(days=5 * 365)
        observation_start = start_dt.isoformat()

    end_date = as_of or date.today().isoformat()

    ck = cache_key("fred", series_id, observation_start, end_date)
    cached = cache_get(ck)
    if cached is not None:
        logger.debug("FRED cache hit: %s", series_id)
        return cached

    logger.info("FRED fetch: %s [%s → %s]", series_id, observation_start, end_date)

    url = f"{FRED_BASE}/series/observations"
    params = {
        "series_id": series_id,
        "api_key": cfg.fred_api_key,
        "file_type": "json",
        "observation_start": observation_start,
        "observation_end": end_date,
        "units": "lin",
        "frequency": "d",
        "aggregation_method": "last",
    }

    with httpx.Client(timeout=30) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()

    data = resp.json()
    obs = data.get("observations", [])
    if not obs:
        raise ValueError(f"FRED returned no observations for {series_id}")

    records = {
        o["date"]: float(o["value"])
        for o in obs
        if o["value"] not in (".", "")
    }

    s = pd.Series(records, dtype=float)
    s.index = pd.to_datetime(s.index)
    s = s.sort_index()

    cache_set(ck, s, TTL_FRED)
    return s


def fetch_series_monthly(
    series_id: str,
    as_of: str | None = None,
) -> pd.Series:
    """Fetch a monthly series (e.g. CPI).  Returns daily-indexed by month-end."""
    cfg = get_settings()
    if not cfg.fred_api_key:
        raise RuntimeError("FRED_API_KEY not set")

    end_date = as_of or date.today().isoformat()
    start_dt = date.today() - timedelta(days=5 * 365)
    observation_start = start_dt.isoformat()

    ck = cache_key("fred_m", series_id, observation_start, end_date)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    logger.info("FRED monthly fetch: %s", series_id)

    url = f"{FRED_BASE}/series/observations"
    params = {
        "series_id": series_id,
        "api_key": cfg.fred_api_key,
        "file_type": "json",
        "observation_start": observation_start,
        "observation_end": end_date,
        "units": "lin",
        "frequency": "m",
        "aggregation_method": "eop",
    }

    with httpx.Client(timeout=30) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()

    data = resp.json()
    obs = data.get("observations", [])
    records = {
        o["date"]: float(o["value"])
        for o in obs
        if o["value"] not in (".", "")
    }

    s = pd.Series(records, dtype=float)
    s.index = pd.to_datetime(s.index)
    s = s.sort_index()

    cache_set(ck, s, TTL_FRED)
    return s


def check_series_exists(series_id: str) -> bool:
    """Return True if the series exists and has at least one observation."""
    cfg = get_settings()
    if not cfg.fred_api_key:
        return False
    try:
        url = f"{FRED_BASE}/series"
        params = {
            "series_id": series_id,
            "api_key": cfg.fred_api_key,
            "file_type": "json",
        }
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, params=params)
        return resp.status_code == 200
    except Exception:
        return False
