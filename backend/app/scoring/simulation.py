from __future__ import annotations

from dataclasses import dataclass

from app.core.models import CardOutput
from app.scoring.aggregate import CardInput, aggregate


@dataclass(frozen=True)
class ScenarioOverrides:
    usd_pct: float = 0.0
    oil_pct: float = 0.0
    yield_bp: float = 0.0
    vix_pct: float = 0.0


_FACTORS = {
    "usd_pct": ("C1", 20.0),
    "yield_bp": ("C2", 100.0),
    "oil_pct": ("C3", 20.0),
    "vix_pct": ("C4", 30.0),
}

_FACTOR_LABELS = {
    "usd_pct": "US dollar",
    "yield_bp": "10-year interest rate",
    "oil_pct": "Oil prices",
    "vix_pct": "Market volatility",
}


def simulate(cards: list[CardOutput], overrides: ScenarioOverrides) -> dict:
    """Apply bounded, illustrative signal adjustments and rerun the core math."""
    card_by_id = {card.id: card for card in cards if card.status == "done"}
    inputs: list[CardInput] = []
    impacts: list[dict] = []

    for card in card_by_id.values():
        signal = card.signal
        for field, (card_id, full_scale) in _FACTORS.items():
            override = getattr(overrides, field)
            if card.id != card_id or override == 0:
                continue
            details = card.math.inputs if card.math else {}
            direction = details.get("d", 0)
            if isinstance(direction, (int, float)) and direction != 0:
                change = max(-0.25, min(0.25, (override / full_scale) * 0.25 * direction))
                signal = max(-1.0, min(1.0, signal + change))
                actual_change = round(signal - card.signal, 4)
                if actual_change == 0:
                    continue
                impacts.append({
                    "card_id": card.id,
                    "factor": field,
                    "signal_change": actual_change,
                })
        inputs.append(CardInput(card.id, signal, card.weight, card.quality))

    result = aggregate(inputs)
    return {
        "composite_signal": result.composite_signal,
        "evidence_strength": result.evidence_strength,
        "coverage": result.coverage,
        "scenario_names": result.scenario_names,
        "scenario_scores": result.scenario_scores,
        "scenario_ci_low": result.scenario_ci_low,
        "scenario_ci_high": result.scenario_ci_high,
        "card_contributions": result.card_contributions,
        "factor_impacts": impacts,
    }


def build_presentation(scenario: dict, baseline: dict | None = None) -> dict:
    """Translate deterministic simulation outputs into stable, plain-language UI copy."""
    signal = scenario["composite_signal"]
    if signal >= 0.15:
        headline = "The evidence leans supportive"
        summary = "Across the available signals, supportive factors outweigh the headwinds."
    elif signal <= -0.15:
        headline = "The evidence points to headwinds"
        summary = "Across the available signals, headwinds outweigh the supportive factors."
    else:
        headline = "The evidence is mixed"
        summary = "The available signals do not point clearly in one direction."

    evidence = scenario["evidence_strength"]
    confidence = "Higher" if evidence >= 0.55 else "Moderate" if evidence >= 0.3 else "Limited"
    baseline_signal = baseline.get("composite_signal", signal) if baseline else signal
    signal_change = signal - baseline_signal
    if signal_change >= 0.02:
        change_summary = "This change makes the outlook somewhat more supportive than the baseline."
    elif signal_change <= -0.02:
        change_summary = "This change makes the outlook somewhat less supportive than the baseline."
    else:
        change_summary = "This change does not materially alter the baseline outlook."
    impacts = sorted(
        scenario["factor_impacts"],
        key=lambda item: (-abs(item["signal_change"]), item["factor"]),
    )
    max_impact = max((abs(item["signal_change"]) for item in impacts), default=0.0)
    drivers = [
        {
            "name": _FACTOR_LABELS[item["factor"]],
            "direction": "supports" if item["signal_change"] > 0 else "weighs on",
            "weight": round(abs(item["signal_change"]) / max_impact * 100) if max_impact else 0,
        }
        for item in impacts
    ]
    return {
        "headline": headline,
        "summary": summary,
        "change_summary": change_summary,
        "confidence_label": confidence,
        "drivers": drivers,
    }
