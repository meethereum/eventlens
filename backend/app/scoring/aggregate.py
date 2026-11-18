"""
EventLens aggregation math — implemented exactly per spec.

e_i  = lambda * w_i * q_i                              (effective evidence per card)
     lambda = 0.6 (discount because cards are correlated)

E_bull    = sum(e_i * max(s_i, 0))                    (evidence for tailwind)
E_bear    = sum(e_i * max(-s_i, 0))                   (evidence for headwind)
E_neutral = sum(e_i * (1 - |s_i|))                    (evidence for neutral)

alpha = 1
p_k = (E_k + alpha) / (E_bull + E_bear + E_neutral + 3*alpha)   (posterior scenario probability)

80% credible interval for each scenario:
  Beta(E_k + alpha, (sum_E - E_k) + 2*alpha)
  10th and 90th percentiles via scipy.stats.beta.ppf

Evidence strength = 1 - H(p) / ln(3)
  where H(p) = -sum(p_k * ln(p_k))  (Shannon entropy)

Coverage K = sum(w_i * q_i) / sum(w_i)

Composite S = sum(w_i * q_i * s_i) / sum(w_i * q_i)

Contribution_i = w_i * q_i * s_i / sum(w_j * q_j)

Scenario names: Tailwind-dominant, Mixed, Headwind-dominant
Label them "evidence-weighted scenario confidence", NEVER "probability the price goes up".
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.stats import beta as beta_dist

LAMBDA = 0.6  # correlation discount
ALPHA = 1.0   # Dirichlet/Beta prior strength


@dataclass
class CardInput:
    """Minimal card representation for aggregation."""
    id: str
    signal: float   # s_i in [-1, 1]
    weight: float    # w_i in [0, 1]
    quality: float   # q_i in [0, 1]


@dataclass
class AggregationResult:
    composite_signal: float
    evidence_strength: float
    coverage: float
    # Scenarios ordered: Tailwind-dominant, Mixed, Headwind-dominant
    scenario_scores: list[float]       # p_k for each
    scenario_ci_low: list[float]       # 10th percentile
    scenario_ci_high: list[float]      # 90th percentile
    scenario_names: list[str]
    card_contributions: dict[str, float]   # card_id → contribution


def aggregate(cards: list[CardInput]) -> AggregationResult:
    """
    Compute the full aggregation from a list of cards.
    Cards with quality=0 or weight=0 are effectively excluded.
    If all cards are excluded, returns uniform distribution.
    """
    # Filter to cards with positive weight and quality
    active = [c for c in cards if c.weight > 0 and c.quality > 0]

    if not active:
        return AggregationResult(
            composite_signal=0.0,
            evidence_strength=0.0,
            coverage=0.0,
            scenario_scores=[1/3, 1/3, 1/3],
            scenario_ci_low=[0.0, 0.0, 0.0],
            scenario_ci_high=[1.0, 1.0, 1.0],
            scenario_names=["Tailwind-dominant", "Mixed", "Headwind-dominant"],
            card_contributions={c.id: 0.0 for c in cards},
        )

    # ── Effective evidence ────────────────────────────────────────────────
    e_i = [LAMBDA * c.weight * c.quality for c in active]
    s_i = [max(min(c.signal, 1.0), -1.0) for c in active]  # clip signals

    # ── Scenario evidence ────────────────────────────────────────────────
    E_bull    = sum(e * max(s, 0) for e, s in zip(e_i, s_i))
    E_bear    = sum(e * max(-s, 0) for e, s in zip(e_i, s_i))
    E_neutral = sum(e * (1 - abs(s)) for e, s in zip(e_i, s_i))

    sum_E = E_bull + E_bear + E_neutral

    # ── Posterior probabilities (Dirichlet-multinomial with uniform prior) ─
    p_bull    = (E_bull + ALPHA) / (sum_E + 3 * ALPHA)
    p_bear    = (E_bear + ALPHA) / (sum_E + 3 * ALPHA)
    p_neutral = (E_neutral + ALPHA) / (sum_E + 3 * ALPHA)

    # ── 80% credible intervals (Beta distribution) ────────────────────────
    # For scenario k: Beta(E_k + alpha, (sum_E - E_k) + 2*alpha)
    ci_bull    = _beta_ci(E_bull, sum_E, ALPHA)
    ci_neutral = _beta_ci(E_neutral, sum_E, ALPHA)
    ci_bear    = _beta_ci(E_bear, sum_E, ALPHA)

    # ── Evidence strength = 1 - H(p) / ln(3) ─────────────────────────────
    p_vals = [p_bull, p_neutral, p_bear]
    H = -sum(p * math.log(p) for p in p_vals if p > 0)
    evidence_strength = 1.0 - H / math.log(3)
    evidence_strength = max(0.0, min(1.0, evidence_strength))

    # ── Coverage K = sum(w_i * q_i) / sum(w_i) ───────────────────────────
    # Per spec: "If a card errors, aggregate over the remaining cards
    # (coverage drops automatically)." This means the denominator
    # includes ALL cards (even failed ones with q=0), so coverage
    # drops when cards fail.
    sum_wq_all = sum(c.weight * c.quality for c in cards)  # all cards, q=0 for failed
    sum_w_all  = sum(c.weight for c in cards)              # all cards
    coverage = sum_wq_all / sum_w_all if sum_w_all > 0 else 0.0

    # sum_wq for active cards only (used in composite and contributions)
    sum_wq = sum_wq_all  # same value since inactive cards have q=0

    # ── Composite S = sum(w_i * q_i * s_i) / sum(w_i * q_i) ──────────────
    if sum_wq > 0:
        composite = sum(c.weight * c.quality * s for c, s in zip(active, s_i)) / sum_wq
    else:
        composite = 0.0
    composite = max(-1.0, min(1.0, composite))

    # ── Card contributions ───────────────────────────────────────────────
    # contribution_i = w_i * q_i * s_i / sum(w_j * q_j)
    contributions: dict[str, float] = {}
    for c, s in zip(active, s_i):
        contributions[c.id] = (c.weight * c.quality * s / sum_wq) if sum_wq > 0 else 0.0

    # Include zero contributions for inactive cards
    for c in cards:
        if c.id not in contributions:
            contributions[c.id] = 0.0

    return AggregationResult(
        composite_signal=round(composite, 6),
        evidence_strength=round(evidence_strength, 6),
        coverage=round(coverage, 6),
        scenario_scores=[round(p_bull, 6), round(p_neutral, 6), round(p_bear, 6)],
        scenario_ci_low=[round(ci_bull[0], 6), round(ci_neutral[0], 6), round(ci_bear[0], 6)],
        scenario_ci_high=[round(ci_bull[1], 6), round(ci_neutral[1], 6), round(ci_bear[1], 6)],
        scenario_names=["Tailwind-dominant", "Mixed", "Headwind-dominant"],
        card_contributions={k: round(v, 6) for k, v in contributions.items()},
    )


def _beta_ci(E_k: float, sum_E: float, alpha: float) -> tuple[float, float]:
    """
    80% credible interval (10th and 90th percentile) from
    Beta(E_k + alpha, (sum_E - E_k) + 2*alpha).
    """
    a = E_k + alpha
    b = (sum_E - E_k) + 2 * alpha

    if a <= 0 or b <= 0:
        return 0.0, 1.0

    try:
        ci_low = float(beta_dist.ppf(0.10, a, b))
        ci_high = float(beta_dist.ppf(0.90, a, b))
    except Exception:
        return 0.0, 1.0

    return ci_low, ci_high


# ---------------------------------------------------------------------------
# Helper: convert CardOutput list → CardInput list → AggregateResult
# ---------------------------------------------------------------------------

def aggregate_from_cards(cards: list) -> AggregationResult:
    """
    Accept a list of CardOutput (Pydantic) objects and run aggregation.
    Only includes cards with status='done'.
    """
    inputs = [
        CardInput(id=c.id, signal=c.signal, weight=c.weight, quality=c.quality)
        for c in cards
        if c.status == "done" and c.id != "_refusal"
    ]
    return aggregate(inputs)
