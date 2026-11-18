"""
C2 — Rates & Inflation

FRED series:
  DGS10    — 10-Year Treasury Constant Maturity Rate
  DFF      — Federal Funds Effective Rate
  T10Y2Y   — 10-Year minus 2-Year Treasury spread
  CPIAUCSL — CPI All Urban Consumers (monthly, YoY computed here)

Metrics: 10y level, 20d change in bp, curve spread, CPI YoY
Signal uses DGS10 as the primary series (absolute change, use_abs=True).
"""
from __future__ import annotations

import time
from datetime import datetime

import numpy as np

from app.core.fred_client import fetch_series, fetch_series_monthly
from app.core.models import CardOutput, Headline, Metric, Source
from app.core.yf_client import fetch_returns
from app.scoring.math import (
    abs_change_over,
    macro_signal,
    series_to_output,
    signal_label,
    trailing_percentile,
    quality_score,
    TAU_DAILY,
    TAU_MONTHLY,
)
from app.scoring.priors import get_prior

CARD_ID    = "C2"
CARD_TITLE = "Rates & Inflation"


def fetch(ticker: str, as_of: str) -> CardOutput:
    t0 = time.time()
    warnings: list[str] = []

    # ── Fetch ──────────────────────────────────────────────────────────────
    dgs10  = fetch_series("DGS10",    as_of=as_of)
    t10y2y = fetch_series("T10Y2Y",   as_of=as_of)
    cpi    = fetch_series_monthly("CPIAUCSL", as_of=as_of)
    stock_ret = fetch_returns(ticker, as_of=as_of)

    # Try DFF but don't fail if unavailable
    try:
        dff = fetch_series("DFF", as_of=as_of)
        fed_funds = round(float(dff.iloc[-1]), 2)
    except Exception:
        fed_funds = None
        warnings.append("DFF (Fed Funds Rate) unavailable")

    # ── Current values ─────────────────────────────────────────────────────
    rate_10y   = round(float(dgs10.iloc[-1]), 3)
    spread     = round(float(t10y2y.iloc[-1]), 3) if len(t10y2y) > 0 else None
    last_date  = dgs10.index[-1].date()

    # ── 20d change in basis points ─────────────────────────────────────────
    delta_20_bp = abs_change_over(dgs10, 20)
    delta_20_bp_rounded = round((delta_20_bp or 0) * 100, 1)  # pct → bp

    # ── CPI YoY ────────────────────────────────────────────────────────────
    cpi_yoy: float | None = None
    if len(cpi) >= 13:
        latest_cpi = float(cpi.iloc[-1])
        prior_cpi  = float(cpi.iloc[-13])
        if prior_cpi > 0:
            cpi_yoy = round((latest_cpi / prior_cpi - 1) * 100, 2)

    # ── Signal ────────────────────────────────────────────────────────────
    # DGS10 is a yield → use absolute change (use_abs=True)
    w_prior = get_prior(CARD_ID, ticker)
    sig = macro_signal(dgs10, stock_ret, L=20, use_abs=True, w_prior=w_prior)

    s = sig["s"]
    w = sig["w"]
    rho = sig["rho"]
    z   = sig["z"]

    # ── Quality ───────────────────────────────────────────────────────────
    fields_ok = sum(x is not None and x == x for x in [rate_10y, delta_20_bp, spread, cpi_yoy])
    q = quality_score(last_date, fields_ok, 4, TAU_DAILY)

    # ── Reasoning ─────────────────────────────────────────────────────────
    bp_str  = f"{delta_20_bp_rounded:+.0f}bp" if delta_20_bp is not None else "N/A"
    spr_str = f"{spread:.2f}%" if spread is not None else "N/A"
    cpi_str = f"{cpi_yoy:.1f}%" if cpi_yoy is not None else "N/A"
    rho_str = f"{rho:.2f}" if rho == rho else "N/A"

    curve_desc = (
        "inverted" if (spread or 0) < 0
        else "flat" if abs(spread or 0) < 0.3
        else "normal"
    )

    reasoning = [
        f"The 10-year Treasury yield stands at {rate_10y:.2f}%, {bp_str} over the past 20 trading days. "
        f"The yield curve is {curve_desc} at {spr_str} (10y–2y spread).",
        f"CPI YoY is {cpi_str}, "
        f"{'above' if (cpi_yoy or 0) > 2.5 else 'near'} the Fed's 2% target — "
        f"{'suggesting rates remain elevated' if (cpi_yoy or 0) > 2.5 else 'giving the Fed room to cut'}.",
        f"The 252-day correlation between {ticker} returns and 10y yield changes is {rho_str}. "
        f"{'High-multiple equities are duration-sensitive; rising yields compress valuations.' if abs(rho or 0) > 0.3 else 'Rate sensitivity for this ticker appears limited in the current window.'}",
        f"Z-score of {z:.2f} vs trailing history → signal s = {s:.2f} "
        f"({'headwind' if s < -0.1 else 'tailwind' if s > 0.1 else 'neutral'} for {ticker}).",
    ]

    latency_ms = int((time.time() - t0) * 1000)

    metrics = [
        Metric(name="10y yield",         value=rate_10y,              unit="%"),
        Metric(name="20d change",         value=delta_20_bp_rounded,   unit="bp"),
        Metric(name="Yield curve (10y–2y)", value=spread,              unit="%"),
        Metric(name="CPI YoY",            value=cpi_yoy,               unit="%"),
    ]
    if fed_funds is not None:
        metrics.append(Metric(name="Fed Funds Rate", value=fed_funds, unit="%"))

    return CardOutput(
        id=CARD_ID,
        title=CARD_TITLE,
        status="done",
        as_of=as_of,
        fetched_at=datetime.utcnow().isoformat() + "Z",
        latency_ms=latency_ms,
        headline=Headline(
            label="10y Treasury",
            value=rate_10y,
            unit="%",
            delta=delta_20_bp_rounded,
        ),
        metrics=metrics,
        series=series_to_output(dgs10.tail(250)),
        signal=round(s, 4),
        label=signal_label(s),
        weight=round(w, 3),
        quality=round(q, 3),
        reasoning=reasoning,
        math={
            "formula": "s = d × tanh(z / 2), Δ in absolute bp (use_abs=True)",
            "inputs": {
                "z":       round(z, 4),
                "rho":     round(rho, 4) if rho == rho else None,
                "d":       sig["d"],
                "w_prior": round(w_prior, 2),
                "delta_bp": delta_20_bp_rounded,
            },
            "contribution": None,
        },
        sources=[
            Source(name="FRED DGS10",    url="https://fred.stlouisfed.org/series/DGS10",    retrieved_at=datetime.utcnow().isoformat() + "Z"),
            Source(name="FRED T10Y2Y",   url="https://fred.stlouisfed.org/series/T10Y2Y",   retrieved_at=datetime.utcnow().isoformat() + "Z"),
            Source(name="FRED CPIAUCSL", url="https://fred.stlouisfed.org/series/CPIAUCSL", retrieved_at=datetime.utcnow().isoformat() + "Z"),
            Source(name="FRED DFF",      url="https://fred.stlouisfed.org/series/DFF",      retrieved_at=datetime.utcnow().isoformat() + "Z"),
        ],
        warnings=warnings,
    )
