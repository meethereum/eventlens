"""
yfinance wrapper.

Fetches adjusted close price history.
Caches for TTL_YFINANCE (1h).
Clips to as_of so cards never use future data.

Note: Yahoo Finance rate-limits aggressively from datacenter IPs.
We set a browser-like User-Agent and retry with backoff on 429.
"""
from __future__ import annotations

import logging
import time
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from app.core.cache import cache_get, cache_key, cache_set, TTL_YFINANCE

logger = logging.getLogger("eventlens.yfinance")

_MAX_RETRIES = 3
_RETRY_DELAY = 2.0  # seconds


def _download_with_retry(ticker: str, **kwargs) -> pd.DataFrame:
    """
    Call yf.download with retry on failure.
    Yahoo returns 429 from datacenter IPs; backing off helps.
    yfinance 1.x handles cookies/crumbs internally with curl_cffi.
    """
    last_exc = None
    for attempt in range(_MAX_RETRIES):
        try:
            df = yf.download(
                ticker,
                progress=False,
                **kwargs,
            )
            if df is not None and not df.empty:
                return df
            # Empty but no exception — retry
            logger.warning("yfinance returned empty for %s (attempt %d)", ticker, attempt + 1)
        except Exception as exc:
            last_exc = exc
            logger.warning("yfinance error for %s (attempt %d): %s", ticker, attempt + 1, str(exc)[:100])

        if attempt < _MAX_RETRIES - 1:
            time.sleep(_RETRY_DELAY * (attempt + 1))

    if last_exc:
        raise last_exc
    return pd.DataFrame()


def fetch_prices(
    ticker: str,
    as_of: str | None = None,
    lookback_days: int = 756 + 60,
) -> pd.Series:
    """
    Return a pandas Series of adjusted close prices for `ticker`,
    from (as_of - lookback_days) to as_of.

    Returns a DatetimeIndex → float series sorted ascending.
    """
    end_date = as_of or date.today().isoformat()
    start_dt = pd.Timestamp(end_date) - pd.Timedelta(days=lookback_days)
    start_date = start_dt.strftime("%Y-%m-%d")

    ck = cache_key("yf", ticker.upper(), start_date, end_date)
    cached = cache_get(ck)
    if cached is not None:
        logger.debug("yfinance cache hit: %s", ticker)
        return cached

    logger.info("yfinance fetch: %s [%s → %s]", ticker, start_date, end_date)

    df = _download_with_retry(
        ticker,
        start=start_date,
        end=end_date,
        auto_adjust=True,
    )

    if df is None or df.empty:
        raise ValueError(f"yfinance returned no data for {ticker}")

    # Flatten multi-index if present (happens with single ticker sometimes)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    close = df["Close"].dropna().sort_index()

    # Clip strictly to as_of
    close = close[close.index <= pd.Timestamp(end_date)]

    cache_set(ck, close, TTL_YFINANCE)
    return close


def fetch_returns(
    ticker: str,
    as_of: str | None = None,
    lookback_days: int = 756 + 60,
) -> pd.Series:
    """Return daily log returns (ln P_t / P_{t-1})."""
    prices = fetch_prices(ticker, as_of, lookback_days)
    import numpy as np
    returns = np.log(prices / prices.shift(1)).dropna()
    return returns


def compute_beta(
    stock_ticker: str,
    market_ticker: str = "SPY",
    as_of: str | None = None,
    window: int = 252,
) -> float:
    """
    Compute trailing `window`-day beta of stock vs market.
    Returns NaN if insufficient data.
    """
    import numpy as np

    try:
        stock_ret = fetch_returns(stock_ticker, as_of).tail(window)
        mkt_ret   = fetch_returns(market_ticker, as_of).tail(window)

        # Align
        combined = pd.concat([stock_ret, mkt_ret], axis=1).dropna()
        combined.columns = ["stock", "mkt"]

        if len(combined) < 60:
            return float("nan")

        cov = combined.cov()
        beta = cov.loc["stock", "mkt"] / cov.loc["mkt", "mkt"]
        return float(beta)
    except Exception as exc:
        logger.warning("Beta computation failed for %s: %s", stock_ticker, exc)
        return float("nan")
