"""
C5 — Sector Relative Strength

Compares the stock's returns vs its sector ETF vs SPY over 5/20/60d.
Rule-based classification:
  company-driven  — stock diverges from sector, sector aligns with SPY
  sector-driven   — sector diverges from SPY, stock moves with sector
  market-driven   — all three move together

Signal s from threshold tables in config/sector_map.yaml, clipped [-1,1].
Weight w fixed at 0.75 (default fundamental card weight).
"""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import numpy as np
import yaml

from app.core.models import CardOutput, Headline, Metric, Source
from app.core.yf_client import fetch_prices
from app.scoring.math import (
    pct_change_over,
    series_to_output,
    signal_label,
    quality_score,
    TAU_DAILY,
)

CARD_ID    = "C5"
CARD_TITLE = "Sector Relative Strength"

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "sector_map.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _get_sector_etf(ticker: str) -> tuple[str, str]:
    cfg = _load_config()
    info = cfg.get("ticker_sector", {}).get(ticker.upper())
    if info:
        return info["etf"], info["sector"]
    return "XLK", "Technology"  # safe fallback


def fetch(ticker: str, as_of: str) -> CardOutput:
    t0 = time.time()
    warnings: list[str] = []

    cfg = _load_config()
    thresholds = cfg.get("c5_thresholds", {})
    company_thresh = thresholds.get("company_alpha_threshold", 3.0)
    sector_thresh  = thresholds.get("sector_alpha_threshold", 2.0)
    signal_thresh  = thresholds.get("signal_threshold", 5.0)

    sector_etf, sector_name = _get_sector_etf(ticker)

    # ── Fetch prices ──────────────────────────────────────────────────────
    stock_prices = fetch_prices(ticker,   as_of=as_of)
    etf_prices   = fetch_prices(sector_etf, as_of=as_of)
    spy_prices   = fetch_prices("SPY",     as_of=as_of)

    # ── Returns over 5/20/60d ──────────────────────────────────────────────
    ret_5  = {tk: pct_change_over(p, 5)  for tk, p in [("stock", stock_prices), ("etf", etf_prices), ("spy", spy_prices)]}
    ret_20 = {tk: pct_change_over(p, 20) for tk, p in [("stock", stock_prices), ("etf", etf_prices), ("spy", spy_prices)]}
    ret_60 = {tk: pct_change_over(p, 60) for tk, p in [("stock", stock_prices), ("etf", etf_prices), ("spy", spy_prices)]}

    # Alphas (stock minus sector, stock minus SPY, sector minus SPY) over 20d
    alpha_stock_vs_sector = (ret_20["stock"] or 0) - (ret_20["etf"] or 0)
    alpha_stock_vs_spy     = (ret_20["stock"] or 0) - (ret_20["spy"] or 0)
    alpha_sector_vs_spy    = (ret_20["etf"] or 0)  - (ret_20["spy"] or 0)

    # ── Driver classification ──────────────────────────────────────────────
    company_driven = abs(alpha_stock_vs_sector) > company_thresh
    sector_driven  = abs(alpha_sector_vs_spy) > sector_thresh and abs(alpha_stock_vs_sector) < company_thresh

    if company_driven:
        classification = "Company-driven"
    elif sector_driven:
        classification = "Sector-driven"
    else:
        classification = "Market-driven"

    # ── Signal ────────────────────────────────────────────────────────────
    # Use alpha_vs_sector / signal_threshold, clipped to [-1, 1]
    s = float(np.clip(alpha_stock_vs_sector / signal_thresh, -1.0, 1.0))

    # Weight: fixed for fundamental cards (0.75 default)
    w = 0.75

    # ── Quality ───────────────────────────────────────────────────────────
    fields_ok = sum(x is not None for x in [ret_5["stock"], ret_20["stock"], ret_60["stock"]])
    last_date = stock_prices.index[-1].date()
    q = quality_score(last_date, fields_ok + 3, 6, TAU_DAILY)  # 6 fields: 3 stock returns + 3 relative

    if ret_5["stock"] is None:
        warnings.append("Insufficient data for 5d return")
    if ret_60["stock"] is None:
        warnings.append("Insufficient data for 60d return")

    latency_ms = int((time.time() - t0) * 1000)

    # ── Reasoning ─────────────────────────────────────────────────────────
    s20 = f"{ret_20['stock']:+.1f}%" if ret_20["stock"] is not None else "N/A"
    e20 = f"{ret_20['etf']:+.1f}%"   if ret_20["etf"]   is not None else "N/A"
    p20 = f"{ret_20['spy']:+.1f}%"   if ret_20["spy"]   is not None else "N/A"

    reasoning = [
        f"{ticker} is {s20} over 20 days vs {sector_etf} {e20} and SPY {p20} — "
        f"an alpha of {alpha_stock_vs_sector:+.1f}pp vs sector and {alpha_stock_vs_spy:+.1f}pp vs SPY.",
        f"Classification: {classification}. "
        f"{'The stock is diverging from its sector, indicating company-specific factors are driving the move.' if classification == 'Company-driven' else 'The sector is moving differently from the broader market, dragging the stock with it.' if classification == 'Sector-driven' else 'All three are moving together; macro is the dominant driver.'}",
        f"Over 60 days {ticker} is {ret_60['stock']:+.1f}% vs {sector_etf} {ret_60['etf']:+.1f}% — "
        f"{'persistent divergence' if abs((ret_60['stock'] or 0) - (ret_60['etf'] or 0)) > 5 else 'converging performance'}.",
        f"Signal s = {s:.2f} ({signal_label(s)}). The relative-strength gap of {alpha_stock_vs_sector:+.1f}pp "
        f"translates to a {'headwind' if s < -0.1 else 'tailwind' if s > 0.1 else 'neutral'} read for {ticker}.",
    ]

    metrics = [
        Metric(name=f"{ticker} 5d",     value=round(ret_5["stock"] or 0, 2),  unit="%"),
        Metric(name=f"{ticker} 20d",    value=round(ret_20["stock"] or 0, 2), unit="%"),
        Metric(name=f"{ticker} 60d",    value=round(ret_60["stock"] or 0, 2), unit="%"),
        Metric(name=f"{sector_etf} 20d", value=round(ret_20["etf"] or 0, 2),   unit="%"),
        Metric(name="SPY 20d",          value=round(ret_20["spy"] or 0, 2),   unit="%"),
        Metric(name="Driver classification", value=classification, unit=""),
    ]

    # Relative strength series (stock / sector ratio)
    rel_series = None
    try:
        aligned = stock_prices.to_frame("stock").join(etf_prices.to_frame("etf"), how="inner")
        rel = (aligned["stock"] / aligned["etf"]) * 100
        rel_series = series_to_output(rel.tail(250))
    except Exception:
        rel_series = []

    return CardOutput(
        id=CARD_ID,
        title=CARD_TITLE,
        status="done",
        as_of=as_of,
        fetched_at=datetime.utcnow().isoformat() + "Z",
        latency_ms=latency_ms,
        headline=Headline(
            label=f"{ticker} vs {sector_etf} (20d)",
            value=round(alpha_stock_vs_sector, 2),
            unit="%",
        ),
        metrics=metrics,
        series=rel_series or series_to_output(stock_prices.tail(250)),
        signal=round(s, 4),
        label=signal_label(s),
        weight=round(w, 3),
        quality=round(q, 3),
        reasoning=reasoning,
        math={
            "formula": "s = clip(alpha_vs_sector / threshold, -1, 1)",
            "inputs": {
                "alpha_vs_sector": round(alpha_stock_vs_sector, 4),
                "alpha_vs_spy":    round(alpha_stock_vs_spy, 4),
                "alpha_sector_vs_spy": round(alpha_sector_vs_spy, 4),
                "threshold":       signal_thresh,
                "classification":  classification,
            },
            "contribution": None,
        },
        sources=[
            Source(name=f"yfinance {ticker}",  url=f"https://finance.yahoo.com/quote/{ticker}",    retrieved_at=datetime.utcnow().isoformat() + "Z"),
            Source(name=f"yfinance {sector_etf}", url=f"https://finance.yahoo.com/quote/{sector_etf}", retrieved_at=datetime.utcnow().isoformat() + "Z"),
            Source(name="yfinance SPY",       url="https://finance.yahoo.com/quote/SPY",            retrieved_at=datetime.utcnow().isoformat() + "Z"),
        ],
        warnings=warnings,
    )
