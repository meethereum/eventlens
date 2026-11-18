"""
Unit tests for app/scoring/math.py

Tests the building blocks:
  - pct_change_over / abs_change_over
  - rolling_changes → compute_z
  - compute_rho
  - macro_signal (s = d × tanh(z/2), w = max(clip(|rho|/0.5, 0.1, 1), w_prior))
  - signal_label
  - freshness_score / quality_score
"""
from __future__ import annotations

import math
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from app.scoring.math import (
    abs_change_over,
    compute_rho,
    compute_z,
    macro_signal,
    pct_change_over,
    quality_score,
    rolling_changes,
    signal_label,
    freshness_score,
    series_to_output,
    TAU_DAILY,
    TAU_MONTHLY,
    TAU_QUARTERLY,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def make_series(values: list[float], start: str = "2024-01-01") -> pd.Series:
    dates = pd.date_range(start, periods=len(values), freq="B")
    return pd.Series(values, index=dates)


# ── pct_change_over ────────────────────────────────────────────────────────

class TestPctChange:
    def test_basic(self):
        s = make_series([100, 101, 102, 103, 104])
        result = pct_change_over(s, L=2)
        # 104/102 - 1 = 0.0196...
        assert result is not None
        assert abs(result - 1.9608) < 0.01

    def test_insufficient_data(self):
        s = make_series([100, 101])
        result = pct_change_over(s, L=5)
        assert result is None

    def test_zero_prior(self):
        # When the prior value (L+1 back) is 0, result should be None
        # Series: [1, 2, 3, 0, 4] with L=1 → prior = s.iloc[-2] = 0
        s = make_series([1.0, 2.0, 3.0, 0.0, 4.0])
        result = pct_change_over(s, L=1)
        assert result is None  # division by zero → None


# ── abs_change_over ───────────────────────────────────────────────────────

class TestAbsChange:
    def test_basic(self):
        s = make_series([4.0, 4.1, 4.2, 4.3, 4.5])
        result = abs_change_over(s, L=2)
        assert result == pytest.approx(0.3, abs=0.001)

    def test_negative_change(self):
        s = make_series([5.0, 4.8, 4.6, 4.4, 4.2])
        result = abs_change_over(s, L=2)
        assert result == pytest.approx(-0.4, abs=0.001)


# ── compute_z ──────────────────────────────────────────────────────────────

class TestComputeZ:
    def test_z_score(self):
        """With a known series, verify z-score calculation."""
        np.random.seed(42)
        values = list(np.random.randn(800) * 0.5 + 0.1)
        s = make_series(values)
        delta, z, std = compute_z(s, L=20, use_abs=False)
        assert delta == pytest.approx(float(s.pct_change(20).iloc[-1] * 100), abs=0.01)
        assert not math.isnan(z)
        assert not math.isnan(std)
        # z should be in a reasonable range for random data
        assert -5 < z < 5

    def test_insufficient_data(self):
        s = make_series([1.0, 2.0, 3.0])
        delta, z, std = compute_z(s, L=20)
        assert math.isnan(z)


# ── compute_rho ───────────────────────────────────────────────────────────

class TestComputeRho:
    def test_correlation(self):
        """Two perfectly correlated series should have rho ≈ 1."""
        np.random.seed(42)
        base = np.cumsum(np.random.randn(300) * 0.01) + 100
        stock_ret = pd.Series(np.diff(base) / base[:-1], index=pd.date_range("2024-01-01", periods=299, freq="B"))
        factor = pd.Series(np.diff(base) / base[:-1], index=pd.date_range("2024-01-01", periods=299, freq="B"))
        rho = compute_rho(stock_ret, factor, window=252)
        assert rho == pytest.approx(1.0, abs=0.01)

    def test_anticorrelated(self):
        """Anti-correlated series should have rho ≈ -1."""
        np.random.seed(42)
        base = np.cumsum(np.random.randn(300) * 0.01) + 100
        stock_ret = pd.Series(np.diff(base) / base[:-1], index=pd.date_range("2024-01-01", periods=299, freq="B"))
        factor = pd.Series(-np.diff(base) / base[:-1], index=pd.date_range("2024-01-01", periods=299, freq="B"))
        rho = compute_rho(stock_ret, factor, window=252)
        assert rho == pytest.approx(-1.0, abs=0.01)

    def test_insufficient_data(self):
        stock_ret = pd.Series([0.01, 0.02], index=pd.date_range("2024-01-01", periods=2, freq="B"))
        factor = pd.Series([0.01, 0.02], index=pd.date_range("2024-01-01", periods=2, freq="B"))
        rho = compute_rho(stock_ret, factor, window=252)
        assert math.isnan(rho)


# ── macro_signal ──────────────────────────────────────────────────────────

class TestMacroSignal:
    def test_signal_bounds(self):
        """Signal s should always be in [-1, 1]."""
        np.random.seed(123)
        factor = make_series(list(np.cumsum(np.random.randn(800) * 0.02) + 100))
        stock_ret = pd.Series(np.random.randn(299) * 0.01, index=pd.date_range("2024-01-01", periods=299, freq="B"))
        result = macro_signal(factor, stock_ret, L=20, use_abs=False, w_prior=0.3)
        assert -1.0 <= result["s"] <= 1.0
        assert 0.1 <= result["w"] <= 1.0  # w is clipped to [0.1, 1] or w_prior

    def test_positive_z_positive_rho(self):
        """Large positive z + positive correlation → positive signal."""
        # Create a series with a strong upward move at the end
        values = [100.0] * 780 + [110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310]
        factor = make_series(values)
        # Stock returns that correlate positively with factor changes
        stock_ret = pd.Series(np.diff(values) / np.array(values[:-1]), index=pd.date_range("2024-01-01", periods=len(values)-1, freq="B"))
        result = macro_signal(factor, stock_ret, L=20, use_abs=False, w_prior=0.3)
        assert result["s"] > 0  # positive signal

    def test_w_prior_floor(self):
        """w should be at least w_prior."""
        np.random.seed(456)
        factor = make_series(list(np.cumsum(np.random.randn(800) * 0.01) + 100))
        stock_ret = pd.Series(np.random.randn(299) * 0.01, index=pd.date_range("2024-01-01", periods=299, freq="B"))
        result = macro_signal(factor, stock_ret, L=20, use_abs=False, w_prior=0.9)
        assert result["w"] >= 0.9

    def test_nan_z_returns_zero_signal(self):
        """If z is NaN (insufficient data), signal should be 0."""
        factor = make_series([100.0, 101.0, 102.0])
        stock_ret = pd.Series([0.01, 0.02], index=pd.date_range("2024-01-01", periods=2, freq="B"))
        result = macro_signal(factor, stock_ret, L=20, use_abs=False, w_prior=0.3)
        assert result["s"] == 0.0


# ── signal_label ──────────────────────────────────────────────────────────

class TestSignalLabel:
    def test_tailwind(self):
        assert signal_label(0.5) == "tailwind"

    def test_headwind(self):
        assert signal_label(-0.5) == "headwind"

    def test_neutral(self):
        assert signal_label(0.05) == "neutral"

    def test_boundary(self):
        assert signal_label(0.1) == "neutral"
        assert signal_label(-0.1) == "neutral"
        assert signal_label(0.11) == "tailwind"
        assert signal_label(-0.11) == "headwind"


# ── freshness / quality ────────────────────────────────────────────────────

class TestQuality:
    def test_freshness_today(self):
        assert freshness_score(date.today(), TAU_DAILY) == pytest.approx(1.0, abs=0.01)

    def test_freshness_old(self):
        old = date.today() - timedelta(days=100)
        f = freshness_score(old, TAU_DAILY)
        assert 0 < f < 0.01  # very low freshness

    def test_quality_score(self):
        q = quality_score(date.today(), 4, 4, TAU_DAILY)
        assert q == pytest.approx(1.0, abs=0.01)

    def test_quality_missing_fields(self):
        q = quality_score(date.today(), 2, 4, TAU_DAILY)
        assert q == pytest.approx(0.5, abs=0.01)

    def test_quality_old_data(self):
        old = date.today() - timedelta(days=100)
        q = quality_score(old, 4, 4, TAU_DAILY)
        assert q < 0.01


# ── series_to_output ───────────────────────────────────────────────────────

class TestSeriesToOutput:
    def test_downsample(self):
        s = pd.Series(range(500), index=pd.date_range("2024-01-01", periods=500, freq="B"))
        out = series_to_output(s, max_points=250)
        assert len(out) <= 250

    def test_small_series(self):
        s = pd.Series([1.0, 2.0, 3.0], index=pd.date_range("2024-01-01", periods=3, freq="B"))
        out = series_to_output(s)
        assert len(out) == 3
        assert out[0]["v"] == 1.0

    def test_empty(self):
        s = pd.Series([], dtype=float)
        out = series_to_output(s)
        assert out == []
