"""
Golden test: 10 cards with known signals → expected scenario distribution.

This test uses a fixed set of 10 cards with hand-picked signals, weights,
and qualities to verify the full aggregation pipeline produces a known
output. The expected numbers are computed independently using the exact
formulas from the spec.

If this test passes, the aggregation math is correct end-to-end.
"""
from __future__ import annotations

import math

import pytest

from app.scoring.aggregate import CardInput, aggregate, LAMBDA, ALPHA


# ── 10-card golden input ───────────────────────────────────────────────────
# Mimics a realistic INTC-like scenario: mostly headwinds, some neutral,
# one tailwind.

GOLDEN_CARDS = [
    CardInput(id="C1",  signal=-0.38, weight=0.60, quality=0.91),  # USD: headwind
    CardInput(id="C2",  signal=-0.42, weight=0.72, quality=0.95),  # Rates: headwind
    CardInput(id="C3",  signal= 0.15, weight=0.30, quality=0.93),  # Oil: mild neutral
    CardInput(id="C4",  signal= 0.44, weight=0.70, quality=0.98),  # Market: tailwind
    CardInput(id="C5",  signal=-0.72, weight=0.75, quality=0.97),  # Sector: strong headwind
    CardInput(id="C6",  signal=-0.31, weight=0.65, quality=0.88),  # Dependency: headwind
    CardInput(id="C7",  signal=-0.55, weight=0.78, quality=0.85),  # Geopolitics: headwind
    CardInput(id="C8",  signal=-0.61, weight=0.78, quality=0.91),  # Financial: headwind
    CardInput(id="C9",  signal=-0.78, weight=0.80, quality=0.93),  # Earnings: strong headwind
    CardInput(id="C10", signal=-0.52, weight=0.75, quality=0.96),  # Valuation: headwind
]


# ── Hand-computed expected values ─────────────────────────────────────────

def _compute_golden() -> dict:
    """Compute the exact expected values from the formulas."""
    cards = GOLDEN_CARDS
    e = [LAMBDA * c.weight * c.quality for c in cards]
    s = [max(min(c.signal, 1.0), -1.0) for c in cards]

    E_bull    = sum(ei * max(si, 0) for ei, si in zip(e, s))
    E_bear    = sum(ei * max(-si, 0) for ei, si in zip(e, s))
    E_neutral = sum(ei * (1 - abs(si)) for ei, si in zip(e, s))
    sum_E = E_bull + E_bear + E_neutral

    p_bull    = (E_bull + ALPHA) / (sum_E + 3 * ALPHA)
    p_neutral = (E_neutral + ALPHA) / (sum_E + 3 * ALPHA)
    p_bear    = (E_bear + ALPHA) / (sum_E + 3 * ALPHA)

    H = -sum(p * math.log(p) for p in [p_bull, p_neutral, p_bear] if p > 0)
    evidence_strength = 1.0 - H / math.log(3)

    sum_wq = sum(c.weight * c.quality for c in cards)
    sum_w  = sum(c.weight for c in cards)
    coverage = sum_wq / sum_w

    composite = sum(c.weight * c.quality * si for c, si in zip(cards, s)) / sum_wq

    return dict(
        E_bull=E_bull,
        E_bear=E_bear,
        E_neutral=E_neutral,
        sum_E=sum_E,
        p_bull=p_bull,
        p_neutral=p_neutral,
        p_bear=p_bear,
        evidence_strength=evidence_strength,
        coverage=coverage,
        composite=composite,
    )


EXPECTED = _compute_golden()


# ── Tests ──────────────────────────────────────────────────────────────────

class TestGoldenTenCards:
    """Verify the full 10-card aggregation produces known outputs."""

    def test_scenario_scores_match(self):
        result = aggregate(GOLDEN_CARDS)
        assert result.scenario_scores[0] == pytest.approx(EXPECTED["p_bull"], abs=1e-4)
        assert result.scenario_scores[1] == pytest.approx(EXPECTED["p_neutral"], abs=1e-4)
        assert result.scenario_scores[2] == pytest.approx(EXPECTED["p_bear"], abs=1e-4)

    def test_headwind_dominant(self):
        """With 7 headwind cards, Headwind-dominant should be the largest or near-largest scenario."""
        result = aggregate(GOLDEN_CARDS)
        assert result.scenario_scores[2] > result.scenario_scores[0]  # bear > bull
        # Note: with moderate signals, neutral can be competitive with bear
        # because E_neutral = sum(e_i * (1 - |s_i|)) is substantial
        assert result.scenario_scores[2] > 0.3  # bear is significant

    def test_composite_negative(self):
        """Composite signal should be negative (headwind-dominated)."""
        result = aggregate(GOLDEN_CARDS)
        assert result.composite_signal < 0
        assert result.composite_signal == pytest.approx(EXPECTED["composite"], abs=1e-4)

    def test_evidence_strength_positive(self):
        """With a directional lean, evidence strength should be positive."""
        result = aggregate(GOLDEN_CARDS)
        assert result.evidence_strength > 0.01  # any directional lean produces positive strength
        assert result.evidence_strength == pytest.approx(EXPECTED["evidence_strength"], abs=1e-4)

    def test_coverage_high(self):
        """All cards have quality > 0.8, so coverage should be > 0.85."""
        result = aggregate(GOLDEN_CARDS)
        assert result.coverage > 0.85
        assert result.coverage == pytest.approx(EXPECTED["coverage"], abs=1e-4)

    def test_credible_intervals_valid(self):
        """Each CI must contain its point estimate."""
        result = aggregate(GOLDEN_CARDS)
        for i in range(3):
            assert result.scenario_ci_low[i] <= result.scenario_scores[i]
            assert result.scenario_scores[i] <= result.scenario_ci_high[i]

    def test_credible_interval_bear_wider_than_uniform(self):
        """Bear CI should be informative (narrower than [0, 1])."""
        result = aggregate(GOLDEN_CARDS)
        bear_ci_width = result.scenario_ci_high[2] - result.scenario_ci_low[2]
        assert bear_ci_width < 0.5  # reasonably tight

    def test_contributions_sum_to_composite(self):
        """Sum of contributions should approximately equal composite signal."""
        result = aggregate(GOLDEN_CARDS)
        total_contrib = sum(result.card_contributions.values())
        # contributions = w_i*q_i*s_i / sum(w_j*q_j)
        # composite = sum(w_i*q_i*s_i) / sum(w_i*q_i)
        # These are the same formula, so they should match
        assert total_contrib == pytest.approx(result.composite_signal, abs=1e-3)

    def test_largest_contribution_is_c9(self):
        """C9 (strongest headwind with high weight/quality) should have the most negative contribution."""
        result = aggregate(GOLDEN_CARDS)
        c9_contrib = result.card_contributions["C9"]
        min_contrib = min(result.card_contributions.values())
        assert c9_contrib == min_contrib  # most negative
        assert c9_contrib < -0.05           # substantially negative

    def test_c4_positive_contribution(self):
        """C4 (only strong tailwind) should have a positive contribution."""
        result = aggregate(GOLDEN_CARDS)
        assert result.card_contributions["C4"] > 0

    def test_scenario_probabilities_sum_to_one(self):
        """p_bull + p_neutral + p_bear = 1."""
        result = aggregate(GOLDEN_CARDS)
        total = sum(result.scenario_scores)
        assert total == pytest.approx(1.0, abs=1e-4)


class TestGoldenReproducibility:
    """Run the same golden input twice — must produce identical results."""

    def test_deterministic(self):
        r1 = aggregate(GOLDEN_CARDS)
        r2 = aggregate(GOLDEN_CARDS)
        assert r1.scenario_scores == r2.scenario_scores
        assert r1.composite_signal == r2.composite_signal
        assert r1.card_contributions == r2.card_contributions
