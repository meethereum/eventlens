"""
Final synthesis — LLM call 2.

Sends compact card JSON + scenario scores to the LLM, which writes an
analyst-style research note.

If the LLM fails or is unconfigured, falls back to a template-based verdict.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime

from pydantic import BaseModel, Field

from app.llm.client import json_completion
from app.core.config import get_settings
from app.core.models import CardOutput, VerdictOutput, Source

logger = logging.getLogger("eventlens.llm.synthesis")


# ---------------------------------------------------------------------------
# Output model (matches the spec's required JSON schema)
# ---------------------------------------------------------------------------

class SynthesisKeyDriver(BaseModel):
    card: str
    point: str

class SynthesisScenario(BaseModel):
    name: str
    score: float
    rationale: str
    watch_for: str

class SynthesisOutput(BaseModel):
    headline: str
    summary: str
    key_drivers: list[SynthesisKeyDriver]
    counter_evidence: list[SynthesisKeyDriver]
    scenarios: list[SynthesisScenario]
    confidence_statement: str
    data_gaps: list[str] = []
    disclaimer: str = ""


# ---------------------------------------------------------------------------
# System prompt (exactly as specified)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a senior equity research analyst writing a short research note. You receive JSON with the user's question, 10 analysis cards (C1 to C10) and precomputed scenario scores. Rules: 1) Use only facts present in the JSON. 2) Cite cards inline like [C3]. 3) Copy scenario scores exactly as given; never invent or alter numbers. 4) Name cards with low weight or quality in data_gaps. 5) Always include counter-evidence, meaning cards that point against the leading scenario. 6) No buy, sell or hold advice and no price targets. 7) If evidence is mixed, say so plainly. Output ONLY valid JSON: {headline, summary (3 to 4 sentences), key_drivers [{card, point}], counter_evidence [{card, point}], scenarios [{name, score, rationale, watch_for}], confidence_statement, data_gaps [], disclaimer}"""


# ---------------------------------------------------------------------------
# Build compact card JSON for the prompt
# ---------------------------------------------------------------------------

def build_compact_cards(cards: dict[str, CardOutput]) -> list[dict]:
    """
    Build compact card JSON for the synthesis prompt.
    Only done cards. Truncates reasoning to 120 chars to stay under token budget.
    """
    compact = []
    for card_id in sorted(cards.keys()):
        if card_id == "_refusal":
            continue
        c = cards[card_id]
        if c.status != "done":
            continue
        compact.append({
            "id": c.id,
            "title": c.title,
            "signal": round(c.signal, 3),
            "label": c.label.value if hasattr(c.label, 'value') else str(c.label),
            "weight": round(c.weight, 3),
            "quality": round(c.quality, 3),
            "headline": {
                "label": c.headline.label if c.headline else "",
                "value": c.headline.value if c.headline else "",
                "unit":  c.headline.unit  if c.headline else "",
            } if c.headline else None,
            "key_metrics": [
                {"name": m.name, "value": m.value, "unit": m.unit}
                for m in c.metrics[:3]
            ],
            # Truncate reasoning to save tokens — 120 chars × 2 strings per card
            "reasoning": [r[:120] for r in c.reasoning[:2]],
            "warnings": c.warnings[:1],
        })
    return compact


def build_scenario_json(aggregate) -> list[dict]:
    """Build scenario scores JSON from AggregateResult."""
    if aggregate is None:
        return []
    return [
        {
            "name": s.name,
            "score": round(s.score, 4),
            "ci_low": round(s.ci_low, 4),
            "ci_high": round(s.ci_high, 4),
        }
        for s in aggregate.scenarios
    ]


# ---------------------------------------------------------------------------
# Build references from card sources (code, not LLM)
# ---------------------------------------------------------------------------

def build_references(cards: dict[str, CardOutput]) -> list[Source]:
    """Collect unique sources from all done cards."""
    seen_urls: set[str] = set()
    refs: list[Source] = []
    for card_id in sorted(cards.keys()):
        if card_id == "_refusal":
            continue
        c = cards[card_id]
        if c.status != "done":
            continue
        for src in c.sources:
            if src.url not in seen_urls:
                refs.append(src)
                seen_urls.add(src.url)
    return refs


# ---------------------------------------------------------------------------
# Citation validator
# ---------------------------------------------------------------------------

def validate_verdict(verdict: SynthesisOutput, cards: dict[str, CardOutput], aggregate) -> bool:
    """
    Light validator:
    1. Every cited [Cn] exists in the card set.
    2. Scenario numbers match the computed math.
    Returns True if valid, False if any check fails.
    """
    valid_card_ids = {cid for cid in cards.keys() if cid != "_refusal"}

    # Check citations in summary, headline, key_drivers, counter_evidence
    all_text = " ".join([
        verdict.headline,
        verdict.summary,
        verdict.confidence_statement,
        " ".join(f"{d.card} {d.point}" for d in verdict.key_drivers),
        " ".join(f"{d.card} {d.point}" for d in verdict.counter_evidence),
    ])

    citations = set()
    import re
    for match in re.finditer(r'\[([C]\d+)\]', all_text):
        citations.add(match.group(1))

    for cite in citations:
        if cite not in valid_card_ids:
            logger.warning("Citation validator: %s does not exist", cite)
            return False

    # Check scenario scores match math
    if aggregate and verdict.scenarios:
        math_scores = {s.name: round(s.score, 4) for s in aggregate.scenarios}
        for vs in verdict.scenarios:
            if vs.name in math_scores:
                if abs(vs.score - math_scores[vs.name]) > 0.01:
                    logger.warning("Citation validator: scenario %s score %s != math %s",
                                  vs.name, vs.score, math_scores[vs.name])
                    return False

    return True


# ---------------------------------------------------------------------------
# Synthesize verdict
# ---------------------------------------------------------------------------

def synthesize_verdict(
    query: str,
    parsed: dict,
    cards: dict[str, CardOutput],
    aggregate,
) -> tuple[VerdictOutput, bool]:
    """
    Call LLM to synthesize the final verdict.
    Returns (verdict, is_verified).
    Falls back to template if LLM fails or is unconfigured.
    """
    cfg = get_settings()

    # Build references from code
    references = build_references(cards)

    if not cfg.llm_api_key:
        return _template_verdict(query, parsed, cards, aggregate, references), False

    compact_cards = build_compact_cards(cards)
    scenario_json = build_scenario_json(aggregate)

    user_prompt_data = {
        "user_question": query,
        "parsed_query": {
            "ticker": parsed.get("ticker", ""),
            "event_type": parsed.get("event_type", ""),
            "as_of": parsed.get("as_of", ""),
            "horizon_days": parsed.get("horizon_days", 20),
        },
        "cards": compact_cards,
        "scenario_scores": scenario_json,
        "composite_signal": round(aggregate.composite_signal, 4) if aggregate else 0,
        "evidence_strength": round(aggregate.evidence_strength, 4) if aggregate else 0,
        "coverage": round(aggregate.coverage, 4) if aggregate else 0,
    }

    import json
    user_prompt = json.dumps(user_prompt_data, indent=2)

    t0 = time.time()
    parsed_llm, raw, used_fallback = json_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_model=SynthesisOutput,
        max_tokens_override=1800,   # synthesis needs more output tokens than parsing
    )
    latency_ms = int((time.time() - t0) * 1000)

    if parsed_llm is None:
        logger.warning("LLM synthesis failed (%dms), using template fallback. Error: %s",
                       latency_ms, str(raw)[:300])
        return _template_verdict(query, parsed, cards, aggregate, references), False

    # Validate citations and scenario numbers
    is_verified = validate_verdict(parsed_llm, cards, aggregate)

    # Convert to VerdictOutput
    verdict = VerdictOutput(
        headline=parsed_llm.headline,
        summary=parsed_llm.summary,
        key_drivers=[{"card": d.card, "point": d.point} for d in parsed_llm.key_drivers],
        counter_evidence=[{"card": d.card, "point": d.point} for d in parsed_llm.counter_evidence],
        scenarios=[{"name": s.name, "score": s.score, "rationale": s.rationale, "watch_for": s.watch_for}
                   for s in parsed_llm.scenarios],
        confidence_statement=parsed_llm.confidence_statement,
        data_gaps=parsed_llm.data_gaps,
        disclaimer=parsed_llm.disclaimer or (
            "This output is for informational and analytical purposes only. "
            "It does not constitute investment advice, a recommendation to buy or sell "
            "any security, or a price target."
        ),
        references=references,
        is_fallback=False,
        model_used=cfg.llm_model if not used_fallback else (cfg.llm_fallback_model or cfg.llm_model),
        is_fallback_model=used_fallback,
    )

    return verdict, is_verified


# ---------------------------------------------------------------------------
# Template fallback verdict
# ---------------------------------------------------------------------------

def _template_verdict(
    query: str,
    parsed: dict,
    cards: dict[str, CardOutput],
    aggregate,
    references: list[Source],
) -> VerdictOutput:
    """Build a template-based verdict from card outputs (no LLM)."""
    done_cards = [c for c in cards.values() if c.status == "done" and c.id != "_refusal"]

    if not done_cards or aggregate is None:
        return VerdictOutput(
            headline="Analysis incomplete",
            summary="Insufficient card data to generate a verdict.",
            is_fallback=True,
            model_used="template",
            disclaimer="This output is for informational purposes only.",
        )

    n_tail = sum(1 for c in done_cards if str(c.label) == "tailwind")
    n_head = sum(1 for c in done_cards if str(c.label) == "headwind")
    n_total = len(done_cards)
    s = aggregate.composite_signal

    dominant = "headwind" if s < -0.1 else "tailwind" if s > 0.1 else "mixed"
    top_drivers = sorted(done_cards, key=lambda c: abs(c.signal * c.weight * c.quality), reverse=True)[:3]

    headline = (
        f"{parsed.get('ticker', '')} faces {n_head}/{n_total} headwind signals across the analysis framework"
        if dominant == "headwind"
        else f"{parsed.get('ticker', '')} shows {n_tail}/{n_total} tailwind signals across the analysis framework"
        if dominant == "tailwind"
        else f"{parsed.get('ticker', '')} shows mixed signals ({n_tail} tailwind, {n_head} headwind)"
    )

    driver_text = ", ".join(
        f"{c.id} ({getattr(c.label, 'value', c.label)}, s={c.signal:.2f})" for c in top_drivers
    )
    summary = (
        f"Across {n_total} cards computed as of {parsed.get('as_of', '')}, "
        f"{parsed.get('ticker', '')} shows a composite signal of {s:+.2f} ({dominant}). "
        f"Top drivers: {driver_text}. "
        f"Evidence strength: {aggregate.evidence_strength:.2f}. "
        f"Coverage: {aggregate.coverage:.2f}. "
        f"This is a template-based verdict; LLM synthesis was unavailable."
    )

    # Build scenario list from aggregate
    scenarios = [
        {
            "name": sc.name,
            "score": sc.score,
            "rationale": sc.rationale or "Computed from evidence-weighted scenario distribution.",
            "watch_for": sc.watch_for or "",
        }
        for sc in aggregate.scenarios
    ]

    return VerdictOutput(
        headline=headline,
        summary=summary,
        key_drivers=[{"card": c.id, "point": c.reasoning[0] if c.reasoning else ""} for c in top_drivers],
        counter_evidence=[
            {"card": c.id, "point": c.reasoning[0] if c.reasoning else ""}
            for c in sorted(done_cards, key=lambda c: c.signal, reverse=True)[:2]
            if c.signal > 0
        ],
        scenarios=scenarios,
        confidence_statement=(
            f"Evidence strength: {aggregate.evidence_strength:.2f}. "
            f"Coverage: {aggregate.coverage:.2f}. "
            f"Composite signal: {s:+.2f}. "
            "Template-based; LLM synthesis unavailable."
        ),
        data_gaps=[f"{c.id}: {'; '.join(c.warnings)}" for c in done_cards if c.warnings],
        disclaimer=(
            "This output is for informational and analytical purposes only. "
            "It does not constitute investment advice, a recommendation to buy or sell "
            "any security, or a price target."
        ),
        references=references,
        is_fallback=True,
        model_used="template (LLM unavailable)",
        is_fallback_model=False,
    )
