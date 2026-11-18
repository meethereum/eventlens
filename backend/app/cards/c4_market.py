"""
C4 — Market Regime & Volatility

Sources:
  yfinance SPY  — S&P 500 ETF (price history)
  FRED VIXCLS   — CBOE Volatility Index (daily)

Metrics:
  SPY 20d/60d return, SPY vs 200-day MA, VIX level, VIX 1y percentile, stock beta

Signal uses VIX (absolute change, use_abs=True) as primary series.
Positive VIX z → fear spike → headwind for equities → d is set by correlation sign.
"""
from __future__ import annotations

import time
from datetime import datetime

import numpy as np
import pandas as pd

from app.core.fred_client import fetch_series
from app.core.models import CardOutput, Headline, Metric, Source
from app.core.yf_client import compute_beta, fetch_prices, fetch_returns
from app.scoring.math import (
    abs_change_over,
    macro_signal,
    pct_change_over,
    series_to_output,
    signal_label,
    trailing_percentile,
    quality_score,
    TAU_DAILY,
)
from app.scoring.priors import get_prior

CARD_ID    = "C4"
CARD_TITLE = "Market Regime & Volatility"


def fetch(ticker: str, as_of: str) -> CardOutput:
    t0 = time.time()
    warnings: list[str] = []

    # ── Fetch ──────────────────────────────────────────────────────────────
    spy_prices  = fetch_prices("SPY", as_of=as_of)
    vix         = fetch_series("VIXCLS", as_of=as_of)
    stock_ret   = fetch_returns(ticker, as_of=as_of)
    spy_ret     = fetch_returns("SPY", as_of=as_of)

    # ── SPY metrics ───────────────────────────────────────────────────────
    spy_20d  = pct_change_over(spy_prices, 20)
    spy_60d  = pct_change_over(spy_prices, 60)

    # SPY vs 200-day MA
    spy_200d_ma: float | None = None
    if len(spy_prices) >= 200:
        ma200 = float(spy_prices.tail(200).mean())
        last_spy = float(spy_prices.iloc[-1])
        spy_200d_ma = round((last_spy / ma200 - 1) * 100, 2)

    # ── VIX metrics ───────────────────────────────────────────────────────
    vix_level = round(float(vix.iloc[-1]), 2)
    vix_pct   = trailing_percentile(vix, 252)
    vix_last_date = vix.index[-1].date()

    # ── Beta ──────────────────────────────────────────────────────────────
    beta = compute_beta(ticker, "SPY", as_of=as_of)
    if beta != beta:
        warnings.append(f"Beta computation failed for {ticker}; using w_prior")

    # ── Signal (VIX-based, absolute change) ───────────────────────────────
    # VIX rises → fear → typically headwind for equities
    # Correlation d captures whether this ticker is hurt (d<0) or helped (d>0)
    w_prior = get_prior(CARD_ID, ticker)
    sig = macro_signal(vix, stock_ret, L=20, use_abs=True, w_prior=w_prior)

    s   = sig["s"]
    w   = sig["w"]
    rho = sig["rho"]
    z   = sig["z"]

    # ── Quality ───────────────────────────────────────────────────────────
    fields_ok = sum(x is not None and x == x
                    for x in [spy_20d, spy_60d, spy_200d_ma, vix_level, vix_pct])
    q = quality_score(vix_last_date, fields_ok, 5, TAU_DAILY)

    # ── Reasoning ─────────────────────────────────────────────────────────
    regime = (
        "bull-market regime" if (spy_200d_ma or 0) > 3 and (spy_20d or 0) > 1
        else "bear-market regime" if (spy_200d_ma or 0) < -5
        else "consolidation phase"
    )
    beta_str = f"{beta:.2f}" if beta == beta else "N/A"
    vix_str  = f"{vix_pct:.0f}th %ile" if vix_pct == vix_pct else "N/A"

    reasoning = [
        f"SPY is {'up' if (spy_20d or 0) > 0 else 'down'} {abs(spy_20d or 0):.1f}% over 20 days "
        f"and {abs(spy_60d or 0):.1f}% over 60 days, trading "
        f"{'above' if (spy_200d_ma or 0) > 0 else 'below'} its 200-day MA by {abs(spy_200d_ma or 0):.1f}% — "
        f"a {regime}.",
        f"VIX is at {vix_level:.1f} ({vix_str}). "
        f"{'Elevated volatility signals broad risk-off; idiosyncratic shocks are amplified.' if vix_pct > 60 else 'Low volatility suggests market calm; company-specific news is more likely to be absorbed quickly.'}",
        f"{ticker} beta vs SPY (252d): {beta_str}. "
        f"{'High beta amplifies both macro tailwinds and headwinds.' if (beta or 0) > 1.2 else 'Below-market beta provides some buffer against broad sell-offs.' if (beta or 0) < 0.8 else 'Near-market beta implies broad market moves translate proportionally.'}",
        f"VIX z-score {z:.2f} → signal s = {s:.2f} "
        f"({'headwind' if s < -0.1 else 'tailwind' if s > 0.1 else 'neutral'}).",
    ]

    latency_ms = int((time.time() - t0) * 1000)

    metrics = [
        Metric(name="SPY 20d return",    value=round(spy_20d or 0, 2),    unit="%"),
        Metric(name="SPY 60d return",    value=round(spy_60d or 0, 2),    unit="%"),
        Metric(name="SPY vs 200d MA",    value=spy_200d_ma,               unit="%"),
        Metric(name="VIX level",         value=vix_level,                 unit=""),
        Metric(name="VIX percentile (1y)", value=round(vix_pct or 0, 0), unit="%ile"),
        Metric(name=f"{ticker} beta (1y)", value=round(beta, 2) if beta == beta else None, unit=""),
    ]

    return CardOutput(
        id=CARD_ID,
        title=CARD_TITLE,
        status="done",
        as_of=as_of,
        fetched_at=datetime.utcnow().isoformat() + "Z",
        latency_ms=latency_ms,
        headline=Headline(
            label="VIX",
            value=vix_level,
            unit="",
            delta=round(abs_change_over(vix, 20) or 0, 2),
        ),
        metrics=metrics,
        series=series_to_output(vix.tail(250)),
        signal=round(s, 4),
        label=signal_label(s),
        weight=round(w, 3),
        quality=round(q, 3),
        reasoning=reasoning,
        math={
            "formula": "s = d × tanh(z / 2), Δ in absolute VIX points",
            "inputs": {
                "z":       round(z, 4),
                "rho":     round(rho, 4) if rho == rho else None,
                "d":       sig["d"],
                "w_prior": round(w_prior, 2),
                "beta":    round(beta, 3) if beta == beta else None,
            },
            "contribution": None,
        },
        sources=[
            Source(name="yfinance SPY",  url="https://finance.yahoo.com/quote/SPY",         retrieved_at=datetime.utcnow().isoformat() + "Z"),
            Source(name="FRED VIXCLS",   url="https://fred.stlouisfed.org/series/VIXCLS",   retrieved_at=datetime.utcnow().isoformat() + "Z"),
        ],
        warnings=warnings,
    )
