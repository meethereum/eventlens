"""
C1 — USD Strength

FRED series: DTWEXBGS (Trade Weighted U.S. Dollar Index: Broad, Goods)
Metrics: level, 20d % change, 60d % change, 1y percentile
"""
from __future__ import annotations

import time
from datetime import datetime

from app.core.fred_client import fetch_series
from app.core.models import CardOutput, Headline, Metric, Source
from app.core.yf_client import fetch_returns
from app.scoring.math import (
    macro_signal,
    pct_change_over,
    series_to_output,
    signal_label,
    trailing_percentile,
    quality_score,
    TAU_DAILY,
)
from app.scoring.priors import get_prior

CARD_ID    = "C1"
CARD_TITLE = "USD Strength"
SERIES_ID  = "DTWEXBGS"


def fetch(ticker: str, as_of: str) -> CardOutput:
    t0 = time.time()
    warnings: list[str] = []

    # ── Fetch ──────────────────────────────────────────────────────────────
    dxy = fetch_series(SERIES_ID, as_of=as_of)
    stock_ret = fetch_returns(ticker, as_of=as_of)

    level = float(dxy.iloc[-1])
    last_date = dxy.index[-1].date()

    # ── Metrics ───────────────────────────────────────────────────────────
    delta_20 = pct_change_over(dxy, 20)
    delta_60 = pct_change_over(dxy, 60)
    pct_1y   = trailing_percentile(dxy, 252)

    # ── Signal ────────────────────────────────────────────────────────────
    w_prior = get_prior(CARD_ID, ticker)
    sig = macro_signal(dxy, stock_ret, L=20, use_abs=False, w_prior=w_prior)

    s     = sig["s"]
    w     = sig["w"]
    rho   = sig["rho"]
    z     = sig["z"]
    delta = sig["delta"]

    # ── Quality ───────────────────────────────────────────────────────────
    fields_ok = sum(x is not None and x == x for x in [level, delta_20, delta_60, pct_1y])
    q = quality_score(last_date, fields_ok, 4, TAU_DAILY)

    if delta_20 is None:
        warnings.append("Insufficient data for 20d change")
    if delta_60 is None:
        warnings.append("Insufficient data for 60d change")

    latency_ms = int((time.time() - t0) * 1000)

    # ── Reasoning ─────────────────────────────────────────────────────────
    d20_str = f"{delta_20:+.1f}%" if delta_20 is not None else "N/A"
    d60_str = f"{delta_60:+.1f}%" if delta_60 is not None else "N/A"
    pct_str = f"{pct_1y:.0f}th" if pct_1y == pct_1y else "N/A"
    rho_str = f"{rho:.2f}" if rho == rho else "N/A"

    reasoning = [
        f"DXY stands at {level:.1f}, having moved {d20_str} over the past 20 trading days "
        f"and sitting at the {pct_str} percentile of its 1-year range.",
        f"The 60-day trend is {d60_str}, suggesting "
        f"{'persistent' if abs(delta_60 or 0) > 1 else 'transitory'} USD direction.",
        f"The 252-day correlation between {ticker} daily returns and USD changes is {rho_str}. "
        f"{'A stronger dollar compresses overseas revenue when translated back to USD.' if (rho or 0) < 0 else 'The company has limited direct USD sensitivity in this window.'}",
        f"Z-score of {z:.2f} vs trailing 756-day distribution implies "
        f"{'above-average' if z > 0 else 'below-average'} USD strength, translating to a "
        f"{'headwind' if s < -0.1 else 'tailwind' if s > 0.1 else 'neutral'} signal of {s:.2f}.",
    ]

    return CardOutput(
        id=CARD_ID,
        title=CARD_TITLE,
        status="done",
        as_of=as_of,
        fetched_at=datetime.utcnow().isoformat() + "Z",
        latency_ms=latency_ms,
        headline=Headline(label="DXY Index", value=round(level, 2), unit="", delta=round(delta_20 or 0, 2)),
        metrics=[
            Metric(name="Level",          value=round(level, 2),         unit=""),
            Metric(name="20d change",     value=round(delta_20 or 0, 2), unit="%"),
            Metric(name="60d change",     value=round(delta_60 or 0, 2), unit="%"),
            Metric(name="1y percentile",  value=round(pct_1y or 0, 0),   unit="%ile"),
        ],
        series=series_to_output(dxy.tail(250)),
        signal=round(s, 4),
        label=signal_label(s),
        weight=round(w, 3),
        quality=round(q, 3),
        reasoning=reasoning,
        math={
            "formula": "s = d × tanh(z / 2);  w = max(clip(|ρ|/0.5, 0.1, 1), w_prior)",
            "inputs": {
                "z":       round(z, 4),
                "rho":     round(rho, 4) if rho == rho else None,
                "d":       sig["d"],
                "w_prior": round(w_prior, 2),
                "delta":   round(delta, 4),
            },
            "contribution": None,  # filled by aggregator
        },
        sources=[
            Source(
                name=f"FRED {SERIES_ID}",
                url=f"https://fred.stlouisfed.org/series/{SERIES_ID}",
                retrieved_at=datetime.utcnow().isoformat() + "Z",
            )
        ],
        warnings=warnings,
    )
