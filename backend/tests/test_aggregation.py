"""
Unit tests for app/scoring/aggregate.py

Golden-number tests with hand-computed expected values.
All tests use the exact formulas from the spec.
"""
from __future__ import annotations

import math

import pytest

from app.scoring.aggregate import (
    CardInput,
    AggregationResult,
    aggregate,
    LAMBDA,
    ALPHA,
)


# ── Helper to compute expected values by hand ──────────────────────────────

def hand_compute(cards: list[CardInput]) -> dict:
    """Manual implementation to cross-check the module."""
    active = [c for c in cards if c.weight > 0 and c.quality > 0]
    if not active:
        return {}

    e_i = [LAMBDA * c.weight * c.quality for c in active]
    s_i = [max(min(c.signal, 1.0), -1.0) for c in active]

    E_bull    = sum(e * max(s, 0) for e, s in zip(e_i, s_i))
    E_bear    = sum(e * max(-s, 0) for e, s in zip(e_i, s_i))
    E_neutral = sum(e * (1 - abs(s)) for e, s in zip(e_i, s_i))
    sum_E = E_bull + E_bear + E_neutral

    p_bull    = (E_bull + ALPHA) / (sum_E + 3 * ALPHA)
    p_neutral = (E_neutral + ALPHA) / (sum_E + 3 * ALPHA)
    p_bear    = (E_bear + ALPHA) / (sum_E + 3 * ALPHA)

    # Shannon entropy
    H = -sum(p * math.log(p) for p in [p_bull, p_neutral, p_bear] if p > 0)
    evidence_strength = 1.0 - H / math.log(3)

    sum_wq = sum(c.weight * c.quality for c in active)
    sum_w  = sum(c.weight for c in active)
    coverage = sum_wq / sum_w if sum_w > 0 else 0.0

    composite = sum(c.weight * c.quality * s for c, s in zip(active, s_i)) / sum_wq if sum_wq > 0 else 0.0

    contributions = {c.id: (c.weight * c.quality * s / sum_wq) if sum_wq > 0 else 0.0
                    for c, s in zip(active, s_i)}

    return dict(
        E_bull=E_bull, E_bear=E_bear, E_neutral=E_neutral,
        p_bull=p_bull, p_neutral=p_neutral, p_bear=p_bear,
        evidence_strength=evidence_strength,
        coverage=coverage, composite=composite,
        contributions=contributions,
    )


# ── Tests ──────────────────────────────────────────────────────────────────

class TestAggregationBasics:
    def test_empty_cards_uniform(self):
        """No cards → uniform distribution, zero evidence."""
        result = aggregate([])
        assert result.composite_signal == 0.0
        assert result.evidence_strength == 0.0
        assert result.coverage == 0.0
        assert result.scenario_scores == [1/3, 1/3, 1/3]

    def test_all_zero_quality_excluded(self):
        """Cards with quality=0 should be excluded → uniform."""
        cards = [CardInput(id="C1", signal=0.5, weight=0.8, quality=0.0)]
        result = aggregate(cards)
        assert result.scenario_scores == [1/3, 1/3, 1/3]
        assert result.card_contributions["C1"] == 0.0

    def test_signal_clipped(self):
        """Signals outside [-1, 1] should be clipped."""
        cards = [CardInput(id="C1", signal=5.0, weight=1.0, quality=1.0)]
        result = aggregate(cards)
        # signal clipped to 1.0 → all evidence in bull
        # With alpha=1 smoothing, p_bull = (e+1)/(e+3) which is < 0.5 for single card
        assert result.scenario_scores[0] > result.scenario_scores[2]  # bull > bear
        assert result.composite_signal <= 1.0


class TestGoldenNumbers:
    """Hand-computed golden numbers for known inputs."""

    def test_single_tailwind_card(self):
        """
        One card: s=0.5, w=0.7, q=0.9
        e = 0.6 * 0.7 * 0.9 = 0.378
        E_bull    = 0.378 * 0.5 = 0.189
        E_bear    = 0.378 * 0   = 0
        E_neutral = 0.378 * 0.5 = 0.189
        sum_E = 0.378
        p_bull    = (0.189 + 1) / (0.378 + 3) = 1.189 / 3.378 = 0.3520
        p_neutral = (0.189 + 1) / 3.378      = 0.3520
        p_bear    = (0 + 1) / 3.378          = 0.2960
        """
        cards = [CardInput(id="C1", signal=0.5, weight=0.7, quality=0.9)]
        result = aggregate(cards)
        expected = hand_compute(cards)

        assert result.scenario_scores[0] == pytest.approx(expected["p_bull"], abs=1e-4)
        assert result.scenario_scores[1] == pytest.approx(expected["p_neutral"], abs=1e-4)
        assert result.scenario_scores[2] == pytest.approx(expected["p_bear"], abs=1e-4)

        # Verify the specific numbers
        assert result.scenario_scores[0] == pytest.approx(0.3520, abs=0.001)
        assert result.scenario_scores[2] == pytest.approx(0.2960, abs=0.001)

    def test_single_headwind_card(self):
        """
        One card: s=-0.8, w=0.8, q=1.0
        e = 0.6 * 0.8 * 1.0 = 0.48
        E_bull    = 0.48 * 0 = 0
        E_bear    = 0.48 * 0.8 = 0.384
        E_neutral = 0.48 * 0.2 = 0.096
        sum_E = 0.48
        p_bull    = 1 / 3.48 = 0.2874
        p_neutral = 1.096 / 3.48 = 0.3149
        p_bear    = 1.384 / 3.48 = 0.3977
        """
        cards = [CardInput(id="C1", signal=-0.8, weight=0.8, quality=1.0)]
        result = aggregate(cards)
        expected = hand_compute(cards)

        assert result.scenario_scores[0] == pytest.approx(expected["p_bull"], abs=1e-4)
        assert result.scenario_scores[2] == pytest.approx(expected["p_bear"], abs=1e-4)

        assert result.scenario_scores[2] == pytest.approx(0.3977, abs=0.001)
        assert result.scenario_scores[0] == pytest.approx(0.2874, abs=0.001)

    def test_two_opposite_cards(self):
        """
        Two cards with opposite signals should produce more neutral than either extreme.
        C1: s=0.6, w=0.7, q=1.0  → e=0.42, E_bull=0.252, E_neutral=0.168
        C2: s=-0.6, w=0.7, q=1.0  → e=0.42, E_bear=0.252, E_neutral=0.168
        sum_E = 0.252 + 0.252 + 0.336 = 0.84
        p_bull    = 1.252 / 3.84 = 0.3260
        p_neutral = 1.336 / 3.84 = 0.3479
        p_bear    = 1.252 / 3.84 = 0.3260
        """
        cards = [
            CardInput(id="C1", signal=0.6, weight=0.7, quality=1.0),
            CardInput(id="C2", signal=-0.6, weight=0.7, quality=1.0),
        ]
        result = aggregate(cards)
        expected = hand_compute(cards)

        assert result.scenario_scores[0] == pytest.approx(expected["p_bull"], abs=1e-4)
        assert result.scenario_scores[1] == pytest.approx(expected["p_neutral"], abs=1e-4)
        assert result.scenario_scores[2] == pytest.approx(expected["p_bear"], abs=1e-4)

        # Neutral should be the largest
        assert result.scenario_scores[1] > result.scenario_scores[0]
        assert result.scenario_scores[1] > result.scenario_scores[2]
        assert result.scenario_scores[1] == pytest.approx(0.3479, abs=0.001)

    def test_evidence_strength_uniform(self):
        """When all scenarios are equal, evidence strength should be 0."""
        cards = [
            CardInput(id="C1", signal=0.5, weight=0.7, quality=0.9),
            CardInput(id="C2", signal=-0.5, weight=0.7, quality=0.9),
        ]
        result = aggregate(cards)
        # Bull and bear are balanced, so evidence strength is low
        assert result.evidence_strength < 0.1

    def test_evidence_strength_extreme(self):
        """When all cards point the same direction, evidence strength should be meaningful."""
        cards = [
            CardInput(id=f"C{i}", signal=0.8, weight=0.7, quality=1.0)
            for i in range(10)
        ]
        result = aggregate(cards)
        # With alpha smoothing and entropy, strength won't reach 0.7 for 10 cards
        # but should be noticeably above 0
        assert result.evidence_strength > 0.1
        # The dominant scenario should be clearly above 50%
        assert result.scenario_scores[0] > 0.5

    def test_coverage(self):
        """
        Coverage K = sum(w_i * q_i) / sum(w_i)
        C1: w=0.8, q=1.0  → wq = 0.8
        C2: w=0.6, q=0.5  → wq = 0.3
        C3: w=0.4, q=0.0  → excluded (q=0)
        K = (0.8 + 0.3 + 0) / (0.8 + 0.6 + 0.4) = 1.1 / 1.8 = 0.6111
        Note: denominator includes ALL cards (even failed), per spec
        "coverage drops automatically" when cards error.
        """
        cards = [
            CardInput(id="C1", signal=0.3, weight=0.8, quality=1.0),
            CardInput(id="C2", signal=-0.2, weight=0.6, quality=0.5),
            CardInput(id="C3", signal=0.1, weight=0.4, quality=0.0),  # excluded
        ]
        result = aggregate(cards)
        assert result.coverage == pytest.approx(0.6111, abs=0.001)

    def test_composite_signal(self):
        """
        Composite S = sum(w_i * q_i * s_i) / sum(w_i * q_i)
        C1: w=0.8, q=1.0, s=0.5  → wqs = 0.4
        C2: w=0.6, q=1.0, s=-0.3 → wqs = -0.18
        S = (0.4 - 0.18) / (0.8 + 0.6) = 0.22 / 1.4 = 0.1571
        """
        cards = [
            CardInput(id="C1", signal=0.5, weight=0.8, quality=1.0),
            CardInput(id="C2", signal=-0.3, weight=0.6, quality=1.0),
        ]
        result = aggregate(cards)
        assert result.composite_signal == pytest.approx(0.1571, abs=0.001)

    def test_contributions(self):
        """
        contribution_i = w_i * q_i * s_i / sum(w_j * q_j)
        C1: w=0.8, q=1.0, s=0.5  → wqs = 0.4,   contrib = 0.4/1.4 = 0.2857
        C2: w=0.6, q=1.0, s=-0.3 → wqs = -0.18, contrib = -0.18/1.4 = -0.1286
        """
        cards = [
            CardInput(id="C1", signal=0.5, weight=0.8, quality=1.0),
            CardInput(id="C2", signal=-0.3, weight=0.6, quality=1.0),
        ]
        result = aggregate(cards)
        assert result.card_contributions["C1"] == pytest.approx(0.2857, abs=0.001)
        assert result.card_contributions["C2"] == pytest.approx(-0.1286, abs=0.001)

    def test_credible_intervals_in_bounds(self):
        """CI low < score < CI high for each scenario."""
        cards = [
            CardInput(id=f"C{i}", signal=0.5 * (-1 if i % 2 == 0 else 1), weight=0.7, quality=0.9)
            for i in range(10)
        ]
        result = aggregate(cards)
        for i in range(3):
            assert 0.0 <= result.scenario_ci_low[i] <= result.scenario_scores[i]
            assert result.scenario_scores[i] <= result.scenario_ci_high[i] <= 1.0


class TestScenarioOrdering:
    def test_names_order(self):
        """Scenarios must be in order: Tailwind, Mixed, Headwind."""
        cards = [CardInput(id="C1", signal=0.5, weight=0.7, quality=0.9)]
        result = aggregate(cards)
        assert result.scenario_names == ["Tailwind-dominant", "Mixed", "Headwind-dominant"]


class TestFailedCardHandling:
    def test_error_card_excluded(self):
        """A card with quality=0 (error) should be excluded from aggregation."""
        cards = [
            CardInput(id="C1", signal=0.5, weight=0.7, quality=1.0),
            CardInput(id="C2", signal=-0.5, weight=0.7, quality=0.0),  # failed
        ]
        result = aggregate(cards)
        # Only C1 counts → bull-leaning distribution
        assert result.scenario_scores[0] > result.scenario_scores[2]
        assert result.card_contributions["C2"] == 0.0

    def test_partial_coverage(self):
        """If some cards fail, coverage should drop."""
        all_cards = [
            CardInput(id=f"C{i}", signal=0.3, weight=0.7, quality=1.0)
            for i in range(10)
        ]
        result_full = aggregate(all_cards)
        assert result_full.coverage == pytest.approx(1.0, abs=0.01)

        # 3 cards fail
        partial = [c if i < 7 else CardInput(id=c.id, signal=c.signal, weight=c.weight, quality=0.0)
                   for i, c in enumerate(all_cards)]
        result_partial = aggregate(partial)
        assert result_partial.coverage < result_full.coverage
