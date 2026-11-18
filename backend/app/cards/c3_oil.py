"""
C3 — Oil & Energy

FRED series:
  DCOILWTICO  — WTI Crude Oil ($/bbl)
  DCOILBRENTEU — Brent Crude Oil ($/bbl)

Metrics: price, 20d change, 60d change, 1y percentile
Signal uses WTI as primary series.
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

CARD_ID    = "C3"
CARD_TITLE = "Oil & Energy"


def fetch(ticker: str, as_of: str) -> CardOutput:
    t0 = time.time()
    warnings: list[str] = []

    # ── Fetch ──────────────────────────────────────────────────────────────
    wti    = fetch_series("DCOILWTICO",   as_of=as_of)
    stock_ret = fetch_returns(ticker, as_of=as_of)

    # Brent is optional
    brent_price: float | None = None
    try:
        brent = fetch_series("DCOILBRENTEU", as_of=as_of)
        brent_price = round(float(brent.iloc[-1]), 2)
    except Exception:
        warnings.append("DCOILBRENTEU (Brent crude) unavailable")

    # ── Metrics ───────────────────────────────────────────────────────────
    wti_price  = round(float(wti.iloc[-1]), 2)
    last_date  = wti.index[-1].date()
    delta_20   = pct_change_over(wti, 20)
    delta_60   = pct_change_over(wti, 60)
    pct_1y     = trailing_percentile(wti, 252)

    # ── Signal ────────────────────────────────────────────────────────────
    w_prior = get_prior(CARD_ID, ticker)
    sig = macro_signal(wti, stock_ret, L=20, use_abs=False, w_prior=w_prior)

    s   = sig["s"]
    w   = sig["w"]
    rho = sig["rho"]
    z   = sig["z"]

    # ── Quality ───────────────────────────────────────────────────────────
    fields_ok = sum(x is not None and x == x for x in [wti_price, delta_20, delta_60, pct_1y])
    q = quality_score(last_date, fields_ok, 4, TAU_DAILY)

    # ── Reasoning ─────────────────────────────────────────────────────────
    d20_str = f"{delta_20:+.1f}%" if delta_20 is not None else "N/A"
    d60_str = f"{delta_60:+.1f}%" if delta_60 is not None else "N/A"
    pct_str = f"{pct_1y:.0f}th"   if pct_1y == pct_1y else "N/A"
    rho_str = f"{rho:.2f}"        if rho == rho else "N/A"

    reasoning = [
        f"WTI crude is at ${wti_price:.2f}/bbl, {d20_str} over 20 days "
        f"and at the {pct_str} percentile of its 1-year range.",
        f"The 60-day trend is {d60_str}, suggesting "
        f"{'sustained directional pressure' if abs(delta_60 or 0) > 5 else 'range-bound conditions'}.",
        f"The {ticker}–WTI 252-day correlation is {rho_str} (prior w = {w_prior}). "
        f"{'Direct commodity producer — high sensitivity.' if w_prior >= 0.9 else 'Indirect exposure via energy costs and downstream demand.' if w_prior >= 0.5 else 'Oil is a secondary cost driver for this company.'}",
        f"Z-score {z:.2f} → signal s = {s:.2f} "
        f"({'headwind' if s < -0.1 else 'tailwind' if s > 0.1 else 'neutral'} for {ticker}).",
    ]

    latency_ms = int((time.time() - t0) * 1000)

    metrics = [
        Metric(name="WTI price",      value=wti_price,                        unit="$/bbl"),
        Metric(name="20d change",     value=round(delta_20 or 0, 2),          unit="%"),
        Metric(name="60d change",     value=round(delta_60 or 0, 2),          unit="%"),
        Metric(name="1y percentile",  value=round(pct_1y or 0, 0),            unit="%ile"),
    ]
    if brent_price is not None:
        metrics.append(Metric(name="Brent price", value=brent_price, unit="$/bbl"))

    return CardOutput(
        id=CARD_ID,
        title=CARD_TITLE,
        status="done",
        as_of=as_of,
        fetched_at=datetime.utcnow().isoformat() + "Z",
        latency_ms=latency_ms,
        headline=Headline(
            label="WTI Crude",
            value=wti_price,
            unit="$/bbl",
            delta=round(delta_20 or 0, 2),
        ),
        metrics=metrics,
        series=series_to_output(wti.tail(250)),
        signal=round(s, 4),
        label=signal_label(s),
        weight=round(w, 3),
        quality=round(q, 3),
        reasoning=reasoning,
        math={
            "formula": "s = d × tanh(z / 2)",
            "inputs": {
                "z":       round(z, 4),
                "rho":     round(rho, 4) if rho == rho else None,
                "d":       sig["d"],
                "w_prior": round(w_prior, 2),
                "delta_pct": round(sig["delta"], 4),
            },
            "contribution": None,
        },
        sources=[
            Source(name="FRED DCOILWTICO",   url="https://fred.stlouisfed.org/series/DCOILWTICO",   retrieved_at=datetime.utcnow().isoformat() + "Z"),
            Source(name="FRED DCOILBRENTEU", url="https://fred.stlouisfed.org/series/DCOILBRENTEU", retrieved_at=datetime.utcnow().isoformat() + "Z"),
        ],
        warnings=warnings,
    )
