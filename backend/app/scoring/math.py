"""
EventLens scoring math — implemented exactly per spec.

Macro cards (C1-C4, C7):
  Δ   = pct change over L=20 trading days
        (for yields and VIX use absolute change)
  z   = (Δ_now - mean(Δ)) / std(Δ),  trailing 756 trading days
  ρ   = Pearson correlation of stock daily returns vs factor daily changes, 252d
  d   = sign(ρ)
  s   = d × tanh(z / 2)        → clipped to [-1, 1]
  w   = max(clip(|ρ| / 0.5, 0.1, 1.0), w_prior)

Data quality:
  freshness   = exp(-age_days / tau)
                tau = 3   (daily series)
                tau = 45  (monthly series)
                tau = 120 (quarterly filings)
  completeness = fields_available / fields_required
  q = freshness × completeness

All functions are pure (no side effects) for easy unit testing.
"""
from __future__ import annotations

import math
from datetime import date

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Signal computation
# ---------------------------------------------------------------------------

def pct_change_over(series: pd.Series, L: int = 20) -> float | None:
    """
    Percentage change of the series over the last L trading-day observations.
    Returns None if insufficient data.
    """
    s = series.dropna()
    if len(s) < L + 1:
        return None
    latest = float(s.iloc[-1])
    prior  = float(s.iloc[-(L + 1)])
    if prior == 0:
        return None
    return (latest - prior) / prior * 100.0


def abs_change_over(series: pd.Series, L: int = 20) -> float | None:
    """Absolute change over L trading-day observations (for yields/VIX)."""
    s = series.dropna()
    if len(s) < L + 1:
        return None
    return float(s.iloc[-1]) - float(s.iloc[-(L + 1)])


def rolling_changes(series: pd.Series, L: int = 20, use_abs: bool = False) -> pd.Series:
    """
    Compute L-period rolling changes across the series.
    use_abs=True for yields/VIX (absolute), False for price series (pct).
    """
    s = series.dropna()
    if use_abs:
        return s.diff(L).dropna()
    else:
        return s.pct_change(L).dropna() * 100.0


def compute_z(
    series: pd.Series,
    L: int = 20,
    lookback: int = 756,
    use_abs: bool = False,
) -> tuple[float, float, float]:
    """
    Returns (delta_now, z_score, std_dev).
    delta_now: the most recent L-period change
    z_score:   (delta_now - mean(all L-period changes over lookback)) / std
    """
    changes = rolling_changes(series, L, use_abs)
    if len(changes) < 30:
        return float("nan"), float("nan"), float("nan")

    # Use only the trailing lookback window
    window = changes.tail(lookback)
    mu  = float(window.mean())
    std = float(window.std())
    if std == 0 or math.isnan(std):
        return float("nan"), float("nan"), float("nan")

    delta_now = float(changes.iloc[-1])
    z = (delta_now - mu) / std
    return delta_now, z, std


def compute_rho(
    stock_returns: pd.Series,
    factor_changes: pd.Series,
    window: int = 252,
) -> float:
    """
    Pearson correlation of stock daily returns vs factor daily changes
    over the last `window` trading days.
    Both series must be aligned by date.
    """
    combined = pd.concat(
        [stock_returns.rename("stock"), factor_changes.rename("factor")],
        axis=1,
    ).dropna()

    if len(combined) < 60:
        return float("nan")

    tail = combined.tail(window)
    rho = tail["stock"].corr(tail["factor"])
    return float(rho) if not math.isnan(rho) else float("nan")


def macro_signal(
    series: pd.Series,
    stock_returns: pd.Series,
    L: int = 20,
    lookback: int = 756,
    use_abs: bool = False,
    w_prior: float = 0.3,
) -> dict:
    """
    Compute full macro card signal.

    Returns:
      delta, z, rho, d, s, w
    """
    delta, z, std = compute_z(series, L, lookback, use_abs)

    if math.isnan(z):
        return dict(delta=delta, z=float("nan"), rho=float("nan"),
                    d=0, s=0.0, w=w_prior, std=float("nan"))

    # Correlation with stock
    factor_changes = rolling_changes(series, 1, use_abs)  # daily changes
    rho = compute_rho(stock_returns, factor_changes)

    if math.isnan(rho):
        d = 0
        rho_clipped = 0.0
    else:
        d = int(math.copysign(1, rho)) if rho != 0 else 0
        rho_clipped = float(np.clip(abs(rho) / 0.5, 0.1, 1.0))

    s = float(d * math.tanh(z / 2))
    s = float(np.clip(s, -1.0, 1.0))
    w = float(max(rho_clipped, w_prior))

    return dict(delta=delta, z=z, rho=rho, d=d, s=s, w=w, std=std)


def signal_label(s: float) -> str:
    if s > 0.1:
        return "tailwind"
    if s < -0.1:
        return "headwind"
    return "neutral"


# ---------------------------------------------------------------------------
# Percentile helpers
# ---------------------------------------------------------------------------

def percentile_rank(series: pd.Series, value: float) -> float:
    """
    Returns the percentile rank (0–100) of `value` within `series`.
    """
    s = series.dropna()
    if len(s) == 0:
        return float("nan")
    return float((s < value).mean() * 100)


def trailing_percentile(series: pd.Series, lookback: int = 252) -> float:
    """Percentile rank of the most recent value vs its trailing lookback."""
    s = series.dropna()
    if len(s) < 2:
        return float("nan")
    window = s.tail(lookback)
    current = float(s.iloc[-1])
    return percentile_rank(window, current)


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

TAU_DAILY     = 3
TAU_MONTHLY   = 45
TAU_QUARTERLY = 120


def freshness_score(last_date: date, tau: int = TAU_DAILY) -> float:
    """exp(-age_days / tau), where age_days = today - last_date."""
    age = (date.today() - last_date).days
    return float(math.exp(-age / tau))


def quality_score(
    last_date: date,
    fields_available: int,
    fields_required: int,
    tau: int = TAU_DAILY,
) -> float:
    """q = freshness × completeness, clamped to [0, 1]."""
    f = freshness_score(last_date, tau)
    c = fields_available / fields_required if fields_required > 0 else 0.0
    return float(np.clip(f * c, 0.0, 1.0))


# ---------------------------------------------------------------------------
# Series → compact output (max 250 points)
# ---------------------------------------------------------------------------

def series_to_output(s: pd.Series, max_points: int = 250) -> list[dict]:
    """Convert a pandas Series to [{t, v}] list, downsampled to max_points."""
    s = s.dropna()
    if len(s) == 0:
        return []
    if len(s) > max_points:
        # Uniform downsample
        idx = np.round(np.linspace(0, len(s) - 1, max_points)).astype(int)
        s = s.iloc[idx]
    return [
        {"t": str(ts.date()) if hasattr(ts, "date") else str(ts), "v": round(float(v), 4)}
        for ts, v in s.items()
    ]
