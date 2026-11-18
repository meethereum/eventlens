"""
C7 — Geopolitical & Policy Risk

Primary source: Caldara-Iacoviello GPR index (daily)
Secondary source: FRED USEPUINDXD (US Economic Policy Uncertainty, monthly)

Metrics: GPR level, 1y percentile, 3m change, sector exposure
Signal: macro_signal on GPR (absolute change, use_abs=True)
Weight: max(clip(|rho|/0.5, 0.1, 1), w_prior from config)
"""
from __future__ import annotations

import time
from datetime import datetime

import numpy as np

from app.core.fred_client import fetch_series_monthly
from app.core.gpr_client import fetch_gpr, get_gpr_metadata
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
)
from app.scoring.priors import get_prior

CARD_ID    = "C7"
CARD_TITLE = "Geopolitical & Policy Risk"


def fetch(ticker: str, as_of: str) -> CardOutput:
    t0 = time.time()
    warnings: list[str] = ["Recent GPR values are preliminary and subject to revision."]

    # ── Fetch GPR ──────────────────────────────────────────────────────────
    gpr = fetch_gpr(as_of=as_of)
    stock_ret = fetch_returns(ticker, as_of=as_of)

    gpr_level = round(float(gpr.iloc[-1]), 2)
    gpr_last_date = gpr.index[-1].date()
    gpr_pct = trailing_percentile(gpr, 252)

    # 3-month change (approx 63 trading days)
    gpr_3m_change: float | None = None
    if len(gpr) >= 64:
        gpr_3m_change = round(float(gpr.iloc[-1]) - float(gpr.iloc[-63]), 2)

    # ── Optional: US Economic Policy Uncertainty (monthly) ──────────────────
    policy_unc: float | None = None
    try:
        epu = fetch_series_monthly("USEPUINDXD", as_of=as_of)
        if len(epu) > 0:
            policy_unc = round(float(epu.iloc[-1]), 1)
    except Exception:
        warnings.append("USEPUINDXD (Economic Policy Uncertainty) unavailable")

    # ── Signal ────────────────────────────────────────────────────────────
    # GPR is an index → absolute change (use_abs=True)
    w_prior = get_prior(CARD_ID, ticker)
    sig = macro_signal(gpr, stock_ret, L=20, use_abs=True, w_prior=w_prior)

    s   = sig["s"]
    w   = sig["w"]
    rho = sig["rho"]
    z   = sig["z"]

    # ── Quality ───────────────────────────────────────────────────────────
    fields_ok = sum(x is not None and x == x for x in [gpr_level, gpr_pct, gpr_3m_change, policy_unc])
    q = quality_score(gpr_last_date, fields_ok, 4, TAU_DAILY)
    q = min(q, 0.85)  # cap — preliminary GPR values

    # ── Reasoning ─────────────────────────────────────────────────────────
    pct_str  = f"{gpr_pct:.0f}th" if gpr_pct == gpr_pct else "N/A"
    chg_str  = f"{gpr_3m_change:+.1f}" if gpr_3m_change is not None else "N/A"
    rho_str  = f"{rho:.2f}" if rho == rho else "N/A"
    exp_str = (
        "Very High" if w_prior >= 0.9
        else "High" if w_prior >= 0.7
        else "Moderate" if w_prior >= 0.5
        else "Low"
    )

    reasoning = [
        f"The GPR index stands at {gpr_level:.1f} — {pct_str} percentile of its 1-year distribution — "
        f"with a 3-month change of {chg_str}.",
        f"{ticker} has a {exp_str.lower()} geopolitical exposure prior (w_prior = {w_prior}). "
        f"{'Direct exposure to geopolitical events via supply chain, export controls, or defense demand.' if w_prior >= 0.7 else 'Indirect exposure via broader market sentiment.' if w_prior >= 0.5 else 'Limited direct geopolitical sensitivity.'}",
        f"The 252-day correlation between {ticker} returns and GPR changes is {rho_str}. "
        f"{'Elevated GPR historically pressures this ticker.' if (rho or 0) < -0.2 else 'GPR sensitivity appears limited in the current window.'}",
        f"Z-score {z:.2f} → signal s = {s:.2f} ({signal_label(s)} for {ticker}). "
        f"Note: recent GPR values are preliminary and may be revised.",
    ]

    latency_ms = int((time.time() - t0) * 1000)

    metrics = [
        Metric(name="GPR level",       value=gpr_level,           unit=""),
        Metric(name="GPR 1y percentile", value=round(gpr_pct or 0, 0), unit="%ile"),
        Metric(name="GPR 3m change",   value=gpr_3m_change,       unit=""),
        Metric(name=f"{ticker} geopolitical exposure", value=exp_str, unit=""),
    ]
    if policy_unc is not None:
        metrics.append(Metric(name="US Policy Uncertainty", value=policy_unc, unit=""))

    # ── Sources ───────────────────────────────────────────────────────────
    gpr_meta = get_gpr_metadata()
    sources = [
        Source(
            name=f"GPR Index ({gpr_meta['attribution']})",
            url=gpr_meta["url"],
            retrieved_at=datetime.utcnow().isoformat() + "Z",
        ),
    ]
    if policy_unc is not None:
        sources.append(Source(
            name="FRED USEPUINDXD",
            url="https://fred.stlouisfed.org/series/USEPUINDXD",
            retrieved_at=datetime.utcnow().isoformat() + "Z",
        ))

    return CardOutput(
        id=CARD_ID,
        title=CARD_TITLE,
        status="done",
        as_of=as_of,
        fetched_at=datetime.utcnow().isoformat() + "Z",
        latency_ms=latency_ms,
        headline=Headline(
            label="GPR Index",
            value=gpr_level,
            unit="",
            delta=gpr_3m_change,
        ),
        metrics=metrics,
        series=series_to_output(gpr.tail(250)),
        signal=round(s, 4),
        label=signal_label(s),
        weight=round(w, 3),
        quality=round(q, 3),
        reasoning=reasoning,
        math={
            "formula": "s = d × tanh(z / 2), Δ in absolute GPR points; w = max(|rho|/0.5, w_prior)",
            "inputs": {
                "z":       round(z, 4),
                "rho":     round(rho, 4) if rho == rho else None,
                "d":       sig["d"],
                "w_prior": round(w_prior, 2),
                "gpr_level": gpr_level,
            },
            "contribution": None,
        },
        sources=sources,
        warnings=warnings,
    )
