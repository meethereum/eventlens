"""
C9 — Earnings & Growth

Source: SEC EDGAR XBRL (annual) + yfinance (earnings-day abnormal return)

Metrics:
  - Revenue YoY (%)
  - Diluted EPS YoY (%)
  - Gross margin trend (improving/declining/stable)
  - Last earnings-day abnormal return (stock minus SPY on earnings day)

Signal: s = clip(0.4×rev_score + 0.4×eps_score + 0.2×abn_ret_score, -1, 1)
Weight: fixed at 0.80 (high importance)
"""
from __future__ import annotations

import time
from datetime import datetime

import numpy as np
import pandas as pd

from app.core.edgar_client import get_annual_value, get_companyfacts
from app.core.models import CardOutput, Headline, Metric, Source
from app.core.yf_client import fetch_prices
from app.scoring.math import pct_change_over, signal_label, quality_score, TAU_QUARTERLY
from app.scoring.thresholds import band_score, get_threshold

CARD_ID    = "C9"
CARD_TITLE = "Earnings & Growth"


def fetch(ticker: str, as_of: str) -> CardOutput:
    t0 = time.time()
    warnings: list[str] = []

    facts = get_companyfacts(ticker, as_of=as_of)

    # ── Revenue (annual, last 2 years for YoY) ────────────────────────────
    rev_concepts = ["us-gaap:Revenues", "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"]
    rev_df = None
    for ck in rev_concepts:
        rev_df = get_annual_value(facts, ck, as_of=as_of, n_years_back=3)
        if not rev_df.empty:
            break

    # ── Diluted EPS (annual, last 2 years) ───────────────────────────────
    eps_concepts = ["us-gaap:EarningsPerShareDiluted", "us-gaap:IncomeLossFromContinuingOperationsPerDilutedShare"]
    eps_df = None
    for ck in eps_concepts:
        eps_df = get_annual_value(facts, ck, as_of=as_of, n_years_back=3)
        if not eps_df.empty:
            break

    # ── Gross profit (for margin trend) ──────────────────────────────────
    gp_df = get_annual_value(facts, "us-gaap:GrossProfit", as_of=as_of, n_years_back=3)

    # ── Compute YoY ──────────────────────────────────────────────────────
    rev_yoy: float | None = None
    if rev_df is not None and not rev_df.empty and "val" in rev_df.columns and len(rev_df) >= 2:
        latest = float(rev_df["val"].iloc[-1])
        prior  = float(rev_df["val"].iloc[-2])
        if prior > 0:
            rev_yoy = (latest / prior - 1) * 100

    eps_yoy: float | None = None
    if eps_df is not None and not eps_df.empty and "val" in eps_df.columns and len(eps_df) >= 2:
        latest = float(eps_df["val"].iloc[-1])
        prior  = float(eps_df["val"].iloc[-2])
        if abs(prior) > 0.001:
            eps_yoy = (latest / prior - 1) * 100

    # ── Gross margin trend ──────────────────────────────────────────────
    margin_trend = "Stable"
    if (gp_df is not None and not gp_df.empty and rev_df is not None and not rev_df.empty
            and "val" in gp_df.columns and len(gp_df) >= 2 and len(rev_df) >= 2):
        try:
            gm_latest = float(gp_df["val"].iloc[-1]) / float(rev_df["val"].iloc[-1]) * 100
            gm_prior  = float(gp_df["val"].iloc[-2]) / float(rev_df["val"].iloc[-2]) * 100
            diff = gm_latest - gm_prior
            if diff > 1.5:
                margin_trend = "Improving"
            elif diff < -1.5:
                margin_trend = "Declining"
        except Exception:
            pass

    # ── Earnings-day abnormal return (stock minus SPY) ───────────────────
    abn_ret: float | None = None
    try:
        stock_prices = fetch_prices(ticker, as_of=as_of, lookback_days=120)
        spy_prices   = fetch_prices("SPY",   as_of=as_of, lookback_days=120)

        # Find the largest single-day move in the last ~60 trading days
        if len(stock_prices) >= 20 and len(spy_prices) >= 20:
            stock_ret = stock_prices.pct_change().dropna().tail(60)
            spy_ret   = spy_prices.pct_change().dropna().tail(60)
            combined  = pd.concat([stock_ret.rename("stock"), spy_ret.rename("spy")], axis=1).dropna()
            if len(combined) >= 10:
                # Earnings day = largest absolute stock return
                earnings_idx = combined["stock"].abs().idxmax()
                stock_move = float(combined.loc[earnings_idx, "stock"]) * 100
                spy_move   = float(combined.loc[earnings_idx, "spy"]) * 100
                abn_ret = round(stock_move - spy_move, 2)
    except Exception as exc:
        warnings.append(f"Earnings-day abnormal return unavailable: {str(exc)[:60]}")

    # ── Signal ───────────────────────────────────────────────────────────
    rev_thresh  = get_threshold("revenue_growth", ticker)
    eps_thresh  = get_threshold("eps_growth", ticker)
    abn_thresh  = get_threshold("abnormal_return", ticker)

    rev_score = band_score(rev_yoy, rev_thresh.get("strong", 15.0), rev_thresh.get("weak", 0.0))
    eps_score = band_score(eps_yoy, eps_thresh.get("strong", 20.0), eps_thresh.get("weak", 0.0))
    abn_score = band_score(abn_ret, abn_thresh.get("strong", 3.0), abn_thresh.get("weak", -3.0))

    weights = get_threshold("c9_weights", ticker) or {"revenue_growth": 0.4, "eps_growth": 0.4, "abnormal_return": 0.2}
    s = float(np.clip(
        weights["revenue_growth"] * rev_score +
        weights["eps_growth"] * eps_score +
        weights["abnormal_return"] * abn_score,
        -1.0, 1.0
    ))
    w = 0.80

    # ── Quality ───────────────────────────────────────────────────────────
    fields_ok = sum(x is not None and x == x for x in [rev_yoy, eps_yoy, margin_trend != "Stable", abn_ret])
    q = quality_score(datetime.now().date(), fields_ok, 4, TAU_QUARTERLY)

    latency_ms = int((time.time() - t0) * 1000)

    # ── Reasoning ─────────────────────────────────────────────────────────
    rev_str = f"{rev_yoy:+.1f}%" if rev_yoy is not None else "N/A"
    eps_str = f"{eps_yoy:+.1f}%" if eps_yoy is not None else "N/A"
    abn_str = f"{abn_ret:+.1f}%" if abn_ret is not None else "N/A"

    reasoning = [
        f"Revenue is {rev_str} YoY and diluted EPS is {eps_str} YoY — "
        f"{'strong growth trajectory' if (rev_yoy or 0) > 10 and (eps_yoy or 0) > 15 else 'declining' if (rev_yoy or 0) < 0 and (eps_yoy or 0) < 0 else 'mixed growth signals'}.",
        f"Gross margin trend is {margin_trend.lower()} based on the last two annual filings.",
        f"The last detected earnings-day abnormal return was {abn_str} (stock minus SPY) — "
        f"{'a positive surprise' if (abn_ret or 0) > 3 else 'a negative surprise' if (abn_ret or 0) < -3 else 'in line with expectations'}.",
        f"Signal s = {s:.2f} ({signal_label(s)}). "
        f"Composite of revenue ({rev_score:.1f}), EPS ({eps_score:.1f}), and abnormal return ({abn_score:.1f}) band scores.",
    ]

    return CardOutput(
        id=CARD_ID,
        title=CARD_TITLE,
        status="done",
        as_of=as_of,
        fetched_at=datetime.utcnow().isoformat() + "Z",
        latency_ms=latency_ms,
        headline=Headline(label="Revenue YoY", value=round(rev_yoy or 0, 2), unit="%"),
        metrics=[
            Metric(name="Revenue YoY", value=round(rev_yoy or 0, 2), unit="%"),
            Metric(name="Diluted EPS YoY", value=round(eps_yoy or 0, 2), unit="%"),
            Metric(name="Gross margin trend", value=margin_trend, unit=""),
            Metric(name="Last earnings abnormal return", value=abn_ret, unit="%"),
        ],
        series=[],
        signal=round(s, 4),
        label=signal_label(s),
        weight=round(w, 3),
        quality=round(q, 3),
        reasoning=reasoning,
        math={
            "formula": "s = clip(0.4×rev_score + 0.4×eps_score + 0.2×abn_ret_score, -1, 1)",
            "inputs": {
                "rev_yoy": round(rev_yoy, 2) if rev_yoy is not None else None,
                "eps_yoy": round(eps_yoy, 2) if eps_yoy is not None else None,
                "abnormal_return": abn_ret,
                "rev_score": round(rev_score, 4),
                "eps_score": round(eps_score, 4),
                "abn_score": round(abn_score, 4),
            },
            "contribution": None,
        },
        sources=[
            Source(
                name=f"SEC EDGAR XBRL ({ticker})",
                url=f"https://data.sec.gov/api/xbrl/companyfacts/",
                retrieved_at=datetime.utcnow().isoformat() + "Z",
            ),
            Source(
                name=f"yfinance {ticker}",
                url=f"https://finance.yahoo.com/quote/{ticker}",
                retrieved_at=datetime.utcnow().isoformat() + "Z",
            ),
        ],
        warnings=warnings,
    )
