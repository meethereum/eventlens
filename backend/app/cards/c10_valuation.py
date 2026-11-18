"""
C10 — Valuation & Price Momentum

Sources:
  yfinance — price history (for 52w range, 50/200d MA)
  SEC EDGAR — TTM diluted EPS (for P/E calculation)

Metrics:
  - P/E TTM (price / TTM diluted EPS from EDGAR)
  - P/E 5y percentile (vs own trailing 5y history)
  - 52-week range position (%)
  - 50d MA trend (above/below)
  - 200d MA trend (above/below)

Signal: s = 0.5×pe_pct_score + 0.3×range_score + 0.2×ma_score, clipped [-1,1]
Weight: fixed at 0.75
"""
from __future__ import annotations

import time
from datetime import datetime

import numpy as np
import pandas as pd

from app.core.edgar_client import get_annual_value, get_companyfacts, get_ttm_value
from app.core.models import CardOutput, Headline, Metric, Source
from app.core.yf_client import fetch_prices
from app.scoring.math import signal_label, quality_score, TAU_DAILY
from app.scoring.thresholds import band_score, get_threshold

CARD_ID     = "C10"
CARD_TITLE  = "Valuation & Price Momentum"


def fetch(ticker: str, as_of: str) -> CardOutput:
    t0 = time.time()
    warnings: list[str] = []

    # ── Price data ────────────────────────────────────────────────────────
    prices = fetch_prices(ticker, as_of=as_of, lookback_days=756 + 60)  # ~3y for 5y P/E history
    latest_price = float(prices.iloc[-1])

    # ── EDGAR: TTM diluted EPS ────────────────────────────────────────────
    facts = get_companyfacts(ticker, as_of=as_of)

    eps_concepts = ["us-gaap:EarningsPerShareDiluted", "us-gaap:IncomeLossFromContinuingOperationsPerDilutedShare"]
    ttm_eps: float | None = None
    for ck in eps_concepts:
        ttm_eps = get_ttm_value(facts, ck, as_of=as_of)
        if ttm_eps is not None:
            break

    # ── P/E TTM ──────────────────────────────────────────────────────────
    pe_ttm: float | None = None
    if ttm_eps and abs(ttm_eps) > 0.001:
        pe_ttm = latest_price / ttm_eps

    # ── P/E 5y percentile ────────────────────────────────────────────────
    # Compute historical P/E by dividing daily price by the TTM EPS at each point.
    # Simplified: use annual EPS and interpolate price on each annual end date.
    pe_5y_pct: float | None = None
    try:
        annual_eps = None
        for ck in eps_concepts:
            annual_eps = get_annual_value(facts, ck, as_of=as_of, n_years_back=5)
            if not annual_eps.empty:
                break

        if annual_eps is not None and not annual_eps.empty and "val" in annual_eps.columns and "end" in annual_eps.columns:
            pe_history = []
            for _, row in annual_eps.iterrows():
                eps_val = float(row["val"])
                eps_date = row["end"]
                if abs(eps_val) > 0.001:
                    # Find closest price on or before eps_date
                    mask = prices.index <= eps_date
                    if mask.any():
                        px = float(prices[mask].iloc[-1])
                        pe_history.append(px / eps_val)

            if len(pe_history) >= 2 and pe_ttm is not None and pe_ttm > 0:
                pe_5y_pct = float(sum(1 for x in pe_history if x < pe_ttm) / len(pe_history) * 100)
    except Exception:
        pass

    if pe_5y_pct is None:
        warnings.append("P/E 5y percentile unavailable (insufficient EPS history)")

    # ── 52-week range position ───────────────────────────────────────────
    range_pct: float | None = None
    try:
        prices_252 = prices.tail(252)
        if len(prices_252) >= 20:
            low_52 = float(prices_252.min())
            high_52 = float(prices_252.max())
            if high_52 > low_52:
                range_pct = float((latest_price - low_52) / (high_52 - low_52) * 100)
    except Exception:
        pass

    # ── 50/200d MA trend ─────────────────────────────────────────────────
    above_50ma = False
    above_200ma = False
    try:
        if len(prices) >= 50:
            ma50 = float(prices.tail(50).mean())
            above_50ma = latest_price > ma50
        if len(prices) >= 200:
            ma200 = float(prices.tail(200).mean())
            above_200ma = latest_price > ma200
    except Exception:
        pass

    # ── Signal ───────────────────────────────────────────────────────────
    pe_thresh  = get_threshold("pe_percentile", ticker)
    range_thresh = get_threshold("range_position", ticker)
    weights = get_threshold("c10_weights", ticker) or {"pe_percentile": 0.5, "range_position": 0.3, "ma_trend": 0.2}

    # P/E percentile: inverted (low percentile = cheap = good)
    pe_score = band_score(pe_5y_pct, pe_thresh.get("strong", 30.0), pe_thresh.get("weak", 70.0), inverted=True)
    # Range position: high = near highs = bullish
    range_score = band_score(range_pct, range_thresh.get("strong", 80.0), range_thresh.get("weak", 20.0))
    # MA trend: above both = +1, below both = -1, mixed = 0
    if above_50ma and above_200ma:
        ma_score = 1.0
    elif not above_50ma and not above_200ma:
        ma_score = -1.0
    else:
        ma_score = 0.0

    s = float(np.clip(
        weights["pe_percentile"] * pe_score +
        weights["range_position"] * range_score +
        weights["ma_trend"] * ma_score,
        -1.0, 1.0
    ))
    w = 0.75

    # ── Quality ───────────────────────────────────────────────────────────
    fields_ok = sum(x is not None and x == x for x in [pe_ttm, pe_5y_pct, range_pct, above_50ma, above_200ma])
    last_date = prices.index[-1].date()
    q = quality_score(last_date, fields_ok, 5, TAU_DAILY)

    latency_ms = int((time.time() - t0) * 1000)

    # ── Reasoning ─────────────────────────────────────────────────────────
    pe_str   = f"{pe_ttm:.1f}x" if pe_ttm else "N/A"
    pct_str  = f"{pe_5y_pct:.0f}th" if pe_5y_pct is not None else "N/A"
    rng_str  = f"{range_pct:.0f}%" if range_pct is not None else "N/A"
    ma50_str = "Above" if above_50ma else "Below"
    ma200_str = "Above" if above_200ma else "Below"

    reasoning = [
        f"P/E TTM is {pe_str}, "
        f"in the {pct_str} percentile of its 5-year history — "
        f"{'cheap relative to its own history' if (pe_5y_pct or 100) < 30 else 'expensive relative to its own history' if (pe_5y_pct or 0) > 70 else 'mid-range valuation'}.",
        f"Trading at the {rng_str} position of its 52-week range — "
        f"{'near highs with positive momentum' if (range_pct or 0) > 80 else 'near lows with bearish momentum' if (range_pct or 0) < 20 else 'mid-range, no strong directional bias'}.",
        f"Price is {ma50_str} the 50-day MA and {ma200_str} the 200-day MA — "
        f"{'a confirmed bullish technical setup' if above_50ma and above_200ma else 'a confirmed bearish technical setup' if not above_50ma and not above_200ma else 'a transitional phase with mixed signals'}.",
        f"Signal s = {s:.2f} ({signal_label(s)}). "
        f"Composite of valuation ({pe_score:.1f}), range ({range_score:.1f}), and MA trend ({ma_score:.1f}).",
    ]

    return CardOutput(
        id=CARD_ID,
        title=CARD_TITLE,
        status="done",
        as_of=as_of,
        fetched_at=datetime.utcnow().isoformat() + "Z",
        latency_ms=latency_ms,
        headline=Headline(label="P/E (TTM)", value=round(pe_ttm or 0, 2), unit="x", delta=None),
        metrics=[
            Metric(name="P/E TTM", value=round(pe_ttm, 2) if pe_ttm else None, unit="x"),
            Metric(name="P/E 5y percentile", value=round(pe_5y_pct, 0) if pe_5y_pct is not None else None, unit="%ile"),
            Metric(name="52-week range position", value=round(range_pct, 0) if range_pct is not None else None, unit="%"),
            Metric(name="50d MA trend", value=ma50_str, unit=""),
            Metric(name="200d MA trend", value=ma200_str, unit=""),
        ],
        series=[],  # could add price series but spec says max 250 points; keep empty for v1
        signal=round(s, 4),
        label=signal_label(s),
        weight=round(w, 3),
        quality=round(q, 3),
        reasoning=reasoning,
        math={
            "formula": "s = 0.5×pe_pct_score + 0.3×range_score + 0.2×ma_score, clipped [-1,1]",
            "inputs": {
                "pe_ttm": round(pe_ttm, 2) if pe_ttm else None,
                "pe_5y_pct": round(pe_5y_pct, 2) if pe_5y_pct is not None else None,
                "range_pct": round(range_pct, 2) if range_pct is not None else None,
                "above_50ma": above_50ma,
                "above_200ma": above_200ma,
                "pe_score": round(pe_score, 4),
                "range_score": round(range_score, 4),
                "ma_score": ma_score,
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
