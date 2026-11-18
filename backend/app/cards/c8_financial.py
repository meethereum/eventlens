"""
C8 — Financial Health

Source: SEC EDGAR XBRL companyfacts

Non-bank metrics:
  - Current ratio (AssetsCurrent / LiabilitiesCurrent)
  - Debt/Equity (LongTermDebt / StockholdersEquity)
  - Interest coverage (OperatingIncome / InterestExpense)
  - Operating margin (OperatingIncome / Revenue)
  - Cash

Bank/broker metrics (JPM, SCHW):
  - Equity/Assets (instead of current ratio)
  - Interest coverage excluded
  - Current ratio marked N/A
  - Operating margin (net interest income / revenue equivalent)

Scoring: s = 0.5 × absolute_band_score + 0.5 × percentile_vs_own_trailing_5y, clipped [-1,1]
Weight: fixed at 0.78 (high importance, fundamental card)
"""
from __future__ import annotations

import time
from datetime import datetime

import numpy as np

from app.core.edgar_client import (
    get_annual_value,
    get_companyfacts,
    get_latest_value,
)
from app.core.models import CardOutput, Headline, Metric, Source
from app.scoring.math import series_to_output, signal_label, quality_score, TAU_QUARTERLY
from app.scoring.thresholds import (
    band_score,
    get_threshold,
    is_bank,
)

CARD_ID    = "C8"
CARD_TITLE = "Financial Health"


def fetch(ticker: str, as_of: str) -> CardOutput:
    t0 = time.time()
    warnings: list[str] = []

    bank = is_bank(ticker)
    if bank:
        warnings.append("Bank sector: current ratio and interest coverage excluded. Using equity/assets.")

    facts = get_companyfacts(ticker, as_of=as_of)

    # ── Extract annual values ─────────────────────────────────────────────
    # Try multiple concept names for each metric
    def _try_concepts(concept_keys: list[str]) -> float | None:
        for ck in concept_keys:
            val = get_latest_value(facts, ck, as_of=as_of)
            if val is not None:
                return val
        return None

    assets_current       = _try_concepts(["us-gaap:AssetsCurrent"])
    liabilities_current  = _try_concepts(["us-gaap:LiabilitiesCurrent"])
    total_assets         = _try_concepts(["us-gaap:Assets"])
    stockholders_equity   = _try_concepts(["us-gaap:StockholdersEquity"])
    long_term_debt       = _try_concepts(["us-gaap:LongTermDebt", "us-gaap:Debt"])
    interest_expense     = _try_concepts(["us-gaap:InterestExpense"])
    operating_income     = _try_concepts(["us-gaap:OperatingIncomeLoss"])
    revenue              = _try_concepts(["us-gaap:Revenues", "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"])
    cash                 = _try_concepts(["us-gaap:CashAndCashEquivalents", "us-gaap:CashAndCashEquivalentsAtCarryingValue"])

    # ── Compute ratios ────────────────────────────────────────────────────
    current_ratio: float | None = None
    if not bank and assets_current and liabilities_current and liabilities_current > 0:
        current_ratio = assets_current / liabilities_current

    equity_assets: float | None = None
    if bank and total_assets and total_assets > 0 and stockholders_equity:
        equity_assets = (stockholders_equity / total_assets) * 100

    debt_equity: float | None = None
    if long_term_debt is not None and stockholders_equity and stockholders_equity > 0:
        debt_equity = long_term_debt / stockholders_equity

    interest_coverage: float | None = None
    if not bank and operating_income is not None and interest_expense and interest_expense != 0:
        interest_coverage = operating_income / abs(interest_expense)

    operating_margin: float | None = None
    if operating_income is not None and revenue and revenue > 0:
        operating_margin = (operating_income / revenue) * 100

    # ── 5-year percentile (historical operating margin) ──────────────────
    pct_5y: float | None = None
    try:
        annual_om = []
        annual_rev = get_annual_value(facts, "us-gaap:Revenues", as_of=as_of, n_years_back=5)
        annual_op = get_annual_value(facts, "us-gaap:OperatingIncomeLoss", as_of=as_of, n_years_back=5)
        if not annual_rev.empty and not annual_op.empty:
            for i in range(min(len(annual_rev), len(annual_op))):
                r = float(annual_rev["val"].iloc[i])
                o = float(annual_op["val"].iloc[i])
                if r > 0:
                    annual_om.append((o / r) * 100)
            if len(annual_om) >= 2 and operating_margin is not None:
                pct_5y = float(sum(1 for x in annual_om if x < operating_margin) / len(annual_om) * 100)
    except Exception:
        pass

    # ── Compute signal ───────────────────────────────────────────────────
    # s = 0.5 × absolute_band_score + 0.5 × percentile_vs_own_trailing_5y

    # Absolute band scores
    if bank:
        ea_thresh = get_threshold("bank_equity_to_assets", ticker)
        band_ea = band_score(equity_assets, ea_thresh.get("strong", 8.0), ea_thresh.get("weak", 5.0))
        om_thresh = get_threshold("bank_operating_margin", ticker)
        band_om = band_score(operating_margin, om_thresh.get("strong", 30.0), om_thresh.get("weak", 15.0))
        abs_score = (band_ea + band_om) / 2
    else:
        ic_thresh = get_threshold("interest_coverage", ticker)
        band_ic = band_score(interest_coverage, ic_thresh.get("strong", 5.0), ic_thresh.get("weak", 2.0))

        cr_thresh = get_threshold("current_ratio", ticker)
        band_cr = band_score(current_ratio, cr_thresh.get("strong", 1.5), cr_thresh.get("weak", 1.0))

        de_thresh = get_threshold("debt_to_equity", ticker)
        band_de = band_score(debt_equity, de_thresh.get("strong", 0.3), de_thresh.get("weak", 2.0), inverted=True)

        abs_score = (band_ic + band_cr + band_de) / 3

    # Percentile score (0-100 → -1 to +1)
    pct_score = (pct_5y / 50 - 1) if pct_5y is not None else 0.0

    s = float(np.clip(0.5 * abs_score + 0.5 * pct_score, -1.0, 1.0))
    w = 0.78

    # ── Quality ───────────────────────────────────────────────────────────
    if bank:
        fields_ok = sum(x is not None and x == x for x in [equity_assets, operating_margin, cash])
        q = quality_score(datetime.now().date(), fields_ok, 4, TAU_QUARTERLY)
    else:
        fields_ok = sum(x is not None and x == x for x in [current_ratio, debt_equity, interest_coverage, operating_margin, cash])
        q = quality_score(datetime.now().date(), fields_ok, 5, TAU_QUARTERLY)

    if current_ratio is None and not bank:
        warnings.append("Current ratio unavailable from EDGAR")
    if interest_coverage is None and not bank:
        warnings.append("Interest coverage unavailable from EDGAR")

    latency_ms = int((time.time() - t0) * 1000)

    # ── Headline ──────────────────────────────────────────────────────────
    if bank:
        hl = Headline(label="Equity/Assets", value=round(equity_assets or 0, 2), unit="%")
    else:
        hl = Headline(label="Interest Coverage", value=round(interest_coverage or 0, 2), unit="x")

    # ── Metrics ───────────────────────────────────────────────────────────
    metrics: list[Metric] = []
    if bank:
        metrics.append(Metric(name="Equity/Assets (CET1 proxy)", value=round(equity_assets or 0, 2), unit="%"))
        metrics.append(Metric(name="Current ratio", value="N/A", unit="", note="Bank — not applicable"))
        metrics.append(Metric(name="Interest coverage", value="N/A", unit="", note="Bank — excluded per sector rules"))
        metrics.append(Metric(name="Operating margin", value=round(operating_margin or 0, 2), unit="%"))
    else:
        metrics.append(Metric(name="Current ratio", value=round(current_ratio or 0, 2), unit="x"))
        metrics.append(Metric(name="Debt/Equity", value=round(debt_equity or 0, 2), unit="x"))
        metrics.append(Metric(name="Interest coverage", value=round(interest_coverage or 0, 2), unit="x"))
        metrics.append(Metric(name="Operating margin", value=round(operating_margin or 0, 2), unit="%"))
    if cash is not None:
        metrics.append(Metric(name="Cash", value=round(cash / 1e9, 2), unit="$B"))

    # ── Reasoning ─────────────────────────────────────────────────────────
    if bank:
        ea_str = f"{equity_assets:.1f}%" if equity_assets else "N/A"
        reasoning = [
            f"Equity/assets (a CET1 proxy) is {ea_str}, "
            f"{'well-capitalized' if (equity_assets or 0) >= 8 else 'adequately capitalized' if (equity_assets or 0) >= 5 else 'undercapitalized'}.",
            f"Operating margin is {operating_margin:.1f}% — "
            f"{'strong' if (operating_margin or 0) >= 25 else 'adequate' if (operating_margin or 0) >= 15 else 'weak'} for a bank.",
            f"Current ratio and interest coverage are marked N/A for banks per sector rules.",
            f"Signal s = {s:.2f} ({signal_label(s)}). Blended from absolute bands and 5-year percentile.",
        ]
    else:
        ic_str = f"{interest_coverage:.1f}x" if interest_coverage else "N/A"
        cr_str = f"{current_ratio:.2f}x" if current_ratio else "N/A"
        om_str = f"{operating_margin:.1f}%" if operating_margin else "N/A"
        reasoning = [
            f"Interest coverage of {ic_str} is in the "
            f"{'strong' if (interest_coverage or 0) >= 5 else 'weak' if (interest_coverage or 0) <= 2 else 'moderate'} band "
            f"(threshold: <2 weak, >5 strong).",
            f"Current ratio at {cr_str} — "
            f"{'healthy liquidity' if (current_ratio or 0) >= 1.5 else 'tight but manageable' if (current_ratio or 0) >= 1.0 else 'working capital stress'}. "
            f"Note: many healthy large caps run below 1.5; the percentile blend accounts for this.",
            f"Operating margin is {om_str}, "
            f"{'well above' if (operating_margin or 0) >= 20 else 'below' if (operating_margin or 0) < 5 else 'near'} the S&P 500 average (~10-12%).",
            f"Signal s = {s:.2f} ({signal_label(s)}). Blended from absolute bands and 5-year percentile.",
        ]

    # ── Sources ──────────────────────────────────────────────────────────
    cik_str = ""
    try:
        from app.core.edgar_client import get_cik
        cik = get_cik(ticker)
        if cik:
            cik_str = f" (CIK {cik})"
    except Exception:
        pass

    return CardOutput(
        id=CARD_ID,
        title=CARD_TITLE,
        status="done",
        as_of=as_of,
        fetched_at=datetime.utcnow().isoformat() + "Z",
        latency_ms=latency_ms,
        headline=hl,
        metrics=metrics,
        series=[],  # no time series for fundamental cards in v1
        signal=round(s, 4),
        label=signal_label(s),
        weight=round(w, 3),
        quality=round(q, 3),
        reasoning=reasoning,
        math={
            "formula": "s = 0.5 × absolute_band_score + 0.5 × pct_vs_5y, clipped [-1,1]",
            "inputs": {
                "bank_sector": bank,
                "abs_band_score": round(abs_score, 4),
                "pct_vs_5y": round(pct_score, 4) if pct_5y is not None else None,
                "interest_coverage": round(interest_coverage, 2) if interest_coverage else None,
                "current_ratio": round(current_ratio, 2) if current_ratio else None,
                "equity_assets": round(equity_assets, 2) if equity_assets else None,
                "operating_margin": round(operating_margin, 2) if operating_margin else None,
            },
            "contribution": None,
        },
        sources=[
            Source(
                name=f"SEC EDGAR XBRL{cik_str}",
                url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_str.replace(' (CIK ', '').replace(')', '')}.json" if cik_str else "",
                retrieved_at=datetime.utcnow().isoformat() + "Z",
            ),
        ],
        warnings=warnings,
    )
