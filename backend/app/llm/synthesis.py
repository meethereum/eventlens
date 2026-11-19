"""Evidence-only overview synthesis and deterministic fallback."""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Literal

from pydantic import BaseModel

from app.core.company_names import COMPANY_NAMES, company_name
from app.core.config import get_settings
from app.core.models import (
    CardOutput,
    OverviewPoint,
    OverviewScenario,
    OverviewWatchItem,
    Source,
    VerdictOutput,
)
from app.cards.plain_language import FACTOR_TITLES, enrich_card
from app.llm.client import json_completion
from app.scoring.thresholds import overview_confidence

logger = logging.getLogger("eventlens.llm.synthesis")


SYSTEM_PROMPT = """You are an analyst explaining a company's situation to someone with no finance background. You get the user's question and findings from 10 checks. Each finding has a title, a plain description, whether it works against or for the company, and how strongly.

Answer the question directly, then explain what matters most and why, in order of importance. Be specific and useful, about 350 to 500 words in total.

Rules:
- Use only the findings you are given. If something would help but is not there, say it is unknown. Never add outside facts, events, laws or products.
- The user's own event (for example, a chief executive leaving) is background they told you, not evidence. Never cite a finding for it.
- Copy numbers exactly as written. Never calculate new ones.
- Write in plain words a teenager would understand. Use the company's name. No ticker symbols, abbreviations, all-caps words or finance jargon. No dashes as punctuation.
- Never say whether to buy, sell or hold, and never predict a price.
- For each point, list the finding ids that support it.

Return only JSON:
{ "headline": max 14 words that answers the question,
  "answer": 3 to 4 sentences on what to expect over the next {horizon} days, described as which way the evidence leans,
  "how_sure": {"reason": 1 to 2 sentences on how much data was available and whether the findings agree},
  "points": [{"title": max 8 words, "explanation": 1 to 2 sentences with exact numbers, "findings": [ids], "direction": "against" or "for", "strength": "strong", "moderate" or "slight"}]
  (4 to 7 items),
  "unknowns": 2 to 4 things this data cannot tell us,
  "watch": [{"what": ..., "why": ..., "findings": [ids]}] (3 items),
  "scenarios": [{"id": "against", "what_it_looks_like": ..., "signs": ...}, {"id": "mixed", ...}, {"id": "for", ...}] }"""


class ModelPoint(BaseModel):
    title: str
    explanation: str
    findings: list[str]
    direction: Literal["against", "for"]
    strength: Literal["strong", "moderate", "slight"]


class ModelWatch(BaseModel):
    what: str
    why: str
    findings: list[str]


class ModelScenario(BaseModel):
    id: Literal["against", "mixed", "for"]
    what_it_looks_like: str
    signs: str


class ModelHowSure(BaseModel):
    reason: str


class SynthesisOutput(BaseModel):
    headline: str
    answer: str
    how_sure: ModelHowSure
    points: list[ModelPoint]
    unknowns: list[str]
    watch: list[ModelWatch]
    scenarios: list[ModelScenario]


def _sanitize(text: str, ticker: str = "") -> str:
    """Replace symbols, abbreviations, and dash marks in user-facing text."""
    normalized = text
    symbols = sorted(COMPANY_NAMES, key=len, reverse=True)
    if ticker and ticker.upper() not in COMPANY_NAMES:
        symbols.insert(0, ticker.upper())
    for symbol in symbols:
        if not symbol:
            continue
        normalized = re.sub(
            rf"\b{re.escape(symbol)}\b",
            company_name(symbol),
            normalized,
            flags=re.IGNORECASE,
        )

    normalized = re.sub(r"\bU\.S\.", "United States", normalized)
    normalized = re.sub(r"\bUS\b", "United States", normalized)
    replacements = {
        "CEO": "chief executive",
        "DXY": "United States dollar",
        "WTI": "oil",
        "VIX": "market volatility",
        "GPR": "world tension",
        "SPY": "the broad United States market",
        "CPI": "prices",
        "EPS": "profit per share",
        "YoY": "compared with a year ago",
        "bp": "basis points",
        "pp": "percentage points",
        "MA": "average price",
        "AI": "artificial intelligence",
        "LLM": "language model",
        "SEC": "company filing",
        "FRED": "public data",
        "SVB": "a large bank",
        "TTM": "the latest year",
        "CET1": "bank owners' funds",
        "S&P": "United States share market",
    }
    for token, replacement in replacements.items():
        normalized = re.sub(rf"\b{re.escape(token)}\b", replacement, normalized, flags=re.IGNORECASE)

    normalized = re.sub(r"\b[A-Z]{2,}\b", lambda match: match.group(0).lower(), normalized)
    normalized = re.sub(r"(?<!\w)[−-](?=\d)", "minus ", normalized)
    normalized = re.sub(r"[‐‑‒–—―]+", ",", normalized)
    normalized = re.sub(r"(?<!\w)[−-](?!\d)", ",", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _word_count(output: SynthesisOutput) -> int:
    texts = [output.headline, output.answer, output.how_sure.reason]
    texts.extend(point.title + " " + point.explanation for point in output.points)
    texts.extend(output.unknowns)
    texts.extend(item.what + " " + item.why for item in output.watch)
    texts.extend(
        scenario.what_it_looks_like + " " + scenario.signs
        for scenario in output.scenarios
    )
    return len(re.findall(r"\b[\w']+\b", " ".join(texts)))


def _number_tokens(text: str) -> set[str]:
    return {
        token.replace(",", "")
        for token in re.findall(r"(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?", text)
    }


def _sentence_count(text: str) -> int:
    return len([sentence for sentence in re.split(r"(?<=[.!?])\s+", text.strip()) if sentence])


def _plain_findings(cards: dict[str, CardOutput], ticker: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for factor_id in FACTOR_TITLES:
        card = cards.get(factor_id)
        if card is None or card.status != "done":
            findings.append({
                "id": factor_id,
                "plain_title": FACTOR_TITLES[factor_id],
                "plain_summary": "The data for this check is not available.",
                "direction": "neutral",
                "strength": "slight",
            })
            continue
        plain = card if card.plain_summary else enrich_card(card, ticker)
        findings.append({
            "id": factor_id,
            "plain_title": _sanitize(plain.plain_title, ticker),
            "plain_summary": _sanitize(plain.plain_summary, ticker),
            "direction": plain.direction,
            "strength": plain.strength,
        })
    return findings


def _validate_output(output: SynthesisOutput, findings: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    valid_ids = {finding["id"] for finding in findings}
    if not 4 <= len(output.points) <= 7:
        errors.append("points must contain four to seven items")
    if not 2 <= len(output.unknowns) <= 4:
        errors.append("unknowns must contain two to four items")
    if len(output.watch) != 3:
        errors.append("watch must contain three items")
    if len(output.scenarios) != 3 or {scenario.id for scenario in output.scenarios} != {"against", "mixed", "for"}:
        errors.append("all three scenario ids are required")
    if len(re.findall(r"\b[\w']+\b", output.headline)) > 14:
        errors.append("headline exceeds fourteen words")
    if not 3 <= _sentence_count(output.answer) <= 4:
        errors.append("answer must contain three to four sentences")
    if _word_count(output) < 250:
        errors.append("overview is shorter than 250 words")
    if not 1 <= _sentence_count(output.how_sure.reason) <= 2:
        errors.append("confidence reason must contain one or two sentences")

    finding_by_id = {finding["id"]: finding for finding in findings}
    for point in output.points:
        if len(re.findall(r"\b[\w']+\b", point.title)) > 8:
            errors.append(f"point {point.title!r} title exceeds eight words")
        if not point.findings or any(finding_id not in valid_ids for finding_id in point.findings):
            errors.append(f"point {point.title!r} has invalid finding ids")
            continue
        cited_text = " ".join(finding_by_id[finding_id]["plain_summary"] for finding_id in point.findings)
        if not _number_tokens(point.title + " " + point.explanation).issubset(_number_tokens(cited_text)):
            errors.append(f"point {point.title!r} contains a number absent from its findings")
        if not any(finding_by_id[finding_id]["direction"] == point.direction for finding_id in point.findings):
            errors.append(f"point {point.title!r} has no finding with the same direction")
        if not 1 <= _sentence_count(point.explanation) <= 2:
            errors.append(f"point {point.title!r} explanation must contain one or two sentences")

    for item in output.watch:
        if not item.findings or any(finding_id not in valid_ids for finding_id in item.findings):
            errors.append("watch item has invalid finding ids")

    visible_text = [output.headline, output.answer, output.how_sure.reason, *output.unknowns]
    visible_text.extend(point.title + " " + point.explanation for point in output.points)
    visible_text.extend(item.what + " " + item.why for item in output.watch)
    visible_text.extend(
        scenario.what_it_looks_like + " " + scenario.signs
        for scenario in output.scenarios
    )
    joined = " ".join(visible_text)
    if re.search(r"\b[A-Z]{2,}\b", joined):
        errors.append("overview contains an all caps word")
    if re.search(r"[\-‐‑‒–—―−]", joined):
        errors.append("overview contains a dash")
    return errors


def _computed_scenario_scores(aggregate) -> dict[str, float]:
    scores = {"against": 0.0, "mixed": 0.0, "for": 0.0}
    if aggregate is None:
        return scores
    for scenario in aggregate.scenarios:
        name = scenario.name.lower()
        if "headwind" in name or "against" in name:
            scores["against"] = float(scenario.score)
        elif "tailwind" in name or "support" in name or "for" in name:
            scores["for"] = float(scenario.score)
        else:
            scores["mixed"] = float(scenario.score)
    return scores


def _scenario_names() -> dict[str, str]:
    return {"against": "Things get harder", "mixed": "A mixed picture", "for": "Things improve"}


def _confidence_reason(coverage: float, agreement: float, level: str, done_count: int = 0) -> str:
    available = f"{done_count} of 10 checks returned data. " if done_count else ""
    if level == "High":
        return available + "The findings point in a similar direction."
    if level == "Medium":
        return available + "Some findings agree, while others are mixed or incomplete."
    return available + "The available findings are limited or do not agree, so this overview is uncertain."


def _assemble_verdict(
    output: SynthesisOutput,
    *,
    ticker: str,
    aggregate,
    references: list[Source],
    is_fallback: bool,
    model_used: str,
    is_fallback_model: bool = False,
) -> VerdictOutput:
    coverage = float(aggregate.coverage) if aggregate is not None else 0.0
    agreement = float(aggregate.evidence_strength) if aggregate is not None else 0.0
    level = overview_confidence(coverage, agreement)
    score_map = _computed_scenario_scores(aggregate)
    scenario_names = _scenario_names()
    scenario_by_id = {scenario.id: scenario for scenario in output.scenarios}
    scenarios = [
        OverviewScenario(
            id=scenario_id,
            name=scenario_names[scenario_id],
            score=score_map[scenario_id],
            what_it_looks_like=_sanitize(
                scenario_by_id[scenario_id].what_it_looks_like, ticker
            ),
            signs=_sanitize(scenario_by_id[scenario_id].signs, ticker),
        )
        for scenario_id in ("against", "mixed", "for")
        if scenario_id in scenario_by_id
    ]
    return VerdictOutput(
        headline=_sanitize(output.headline, ticker),
        answer=_sanitize(output.answer, ticker),
        summary=_sanitize(output.answer, ticker),
        how_sure_level=level,
        how_sure_reason=_sanitize(output.how_sure.reason, ticker),
        points=[
            OverviewPoint(
                title=_sanitize(point.title, ticker),
                explanation=_sanitize(point.explanation, ticker),
                findings=point.findings,
                direction=point.direction,
                strength=point.strength,
            )
            for point in output.points
        ],
        unknowns=[_sanitize(text, ticker) for text in output.unknowns],
        watch=[
            OverviewWatchItem(
                what=_sanitize(item.what, ticker),
                why=_sanitize(item.why, ticker),
                findings=item.findings,
            )
            for item in output.watch
        ],
        scenarios=scenarios,
        scenario_split=score_map,
        references=references,
        is_fallback=is_fallback,
        model_used=model_used,
        is_fallback_model=is_fallback_model,
    )


def _fallback_output(
    query: str,
    parsed: dict,
    findings: list[dict[str, str]],
    aggregate,
    cards: dict | None = None,
) -> SynthesisOutput:
    ticker = str(parsed.get("ticker", ""))
    company = company_name(ticker)
    event = _sanitize(str(parsed.get("event_type", "company event")), ticker)
    horizon = int(parsed.get("horizon_days", 20) or 20)
    signal = float(aggregate.composite_signal) if aggregate is not None else 0.0
    overall = "against" if signal < -0.1 else "for" if signal > 0.1 else "mixed"
    overall_words = {"against": "negative", "mixed": "mixed", "for": "positive"}
    available = [
        finding for finding in findings
        if finding["direction"] != "neutral"
    ]
    strength_rank = {"strong": 0, "moderate": 1, "slight": 2}
    signal_by_id = {card.id: abs(card.signal) for card in cards.values()} if cards else {}
    available.sort(key=lambda finding: (
        strength_rank.get(finding["strength"], 3),
        -signal_by_id.get(finding["id"], 0.0),
        finding["id"],
    ))
    selected = available[:5]
    if len(selected) < 4:
        neutral = [finding for finding in findings if finding not in selected]
        selected.extend(neutral[:4 - len(selected)])

    points: list[ModelPoint] = []
    for finding in selected:
        if finding["direction"] == "neutral":
            continue
        points.append(ModelPoint(
            title=finding["plain_title"],
            explanation=(
                f"{finding['plain_summary']} This currently points {finding['direction']} the company "
                f"with a {finding['strength']} reading."
            ),
            findings=[finding["id"]],
            direction=finding["direction"],
            strength=finding["strength"],
        ))

    points = points[:7]

    primary = selected[0] if selected else findings[0]
    unknowns = [
        "These checks cannot establish whether the event caused a later share price move.",
        "They cannot show what company leaders will do next or whether future results will change.",
        "They do not measure every supplier, customer, or decision that could affect the company.",
    ]
    watch: list[ModelWatch] = []
    watch_findings = selected[:3] if selected else findings[:3]
    for finding in watch_findings:
        watch.append(ModelWatch(
            what=finding["plain_title"],
            why=finding["plain_summary"],
            findings=[finding["id"]],
        ))
    scenarios = [
        ModelScenario(
            id="against",
            what_it_looks_like="The findings that work against the company remain more important.",
            signs=next((point.explanation for point in points if point.direction == "against"), "No clear signs are available."),
        ),
        ModelScenario(
            id="mixed",
            what_it_looks_like="Findings continue to point in different directions.",
            signs="The available checks do not settle on one direction.",
        ),
        ModelScenario(
            id="for",
            what_it_looks_like="The findings that support the company remain more important.",
            signs=next((point.explanation for point in points if point.direction == "for"), "No clear signs are available."),
        ),
    ]
    done_count = sum(card.status == "done" for card in cards.values())
    level = overview_confidence(
        float(aggregate.coverage) if aggregate is not None else 0.0,
        float(aggregate.evidence_strength) if aggregate is not None else 0.0,
    )
    reason = _confidence_reason(
        float(aggregate.coverage) if aggregate is not None else 0.0,
        float(aggregate.evidence_strength) if aggregate is not None else 0.0,
        level,
        done_count,
    )
    answer = (
        f"After the {event} you described, the current evidence for {company} is {overall_words[overall]}. "
        f"Over the next {horizon} days, the evidence leans {overall_words[overall]}, not toward a definite outcome. "
        f"The most relevant available check is {primary['plain_title']}: {primary['plain_summary']} "
        "This describes the supplied information only and does not establish what caused the event or what will happen next."
    )
    return SynthesisOutput(
        headline=f"{company}'s evidence after the event is {overall_words[overall]}",
        answer=answer,
        how_sure=ModelHowSure(reason=reason),
        points=points,
        unknowns=unknowns,
        watch=watch,
        scenarios=scenarios,
    )


def _build_fallback(
    query: str,
    parsed: dict,
    cards: dict[str, CardOutput],
    aggregate,
    references: list[Source],
) -> VerdictOutput:
    ticker = str(parsed.get("ticker", ""))
    findings = _plain_findings(cards, ticker)
    output = _fallback_output(query, parsed, findings, aggregate, cards)
    # The fallback is deterministic, so never block it on language-model validation.
    return _assemble_verdict(
        output,
        ticker=ticker,
        aggregate=aggregate,
        references=references,
        is_fallback=True,
        model_used="plain evidence summary",
    )


def _build_references(cards: dict[str, CardOutput]) -> list[Source]:
    seen_urls: set[str] = set()
    references: list[Source] = []
    for card in cards.values():
        for source in card.sources:
            if source.url and source.url not in seen_urls:
                references.append(source)
                seen_urls.add(source.url)
    return references


def _validate_and_clean(
    output: SynthesisOutput,
    findings: list[dict[str, str]],
    ticker: str,
    event_text: str,
) -> SynthesisOutput:
    """Sanitize model text before checking its claims and formatting."""
    output = output.model_copy(update={
        "headline": _sanitize(output.headline, ticker),
        "answer": _sanitize(output.answer, ticker),
        "how_sure": ModelHowSure(reason=_sanitize(output.how_sure.reason, ticker)),
        "points": [point.model_copy(update={
            "title": _sanitize(point.title, ticker),
            "explanation": _sanitize(point.explanation, ticker),
        }) for point in output.points],
        "unknowns": [_sanitize(text, ticker) for text in output.unknowns],
        "watch": [item.model_copy(update={
            "what": _sanitize(item.what, ticker),
            "why": _sanitize(item.why, ticker),
        }) for item in output.watch],
        "scenarios": [scenario.model_copy(update={
            "what_it_looks_like": _sanitize(scenario.what_it_looks_like, ticker),
            "signs": _sanitize(scenario.signs, ticker),
        }) for scenario in output.scenarios],
    })
    errors = _validate_output(output, findings)
    event_terms = {
        word for word in re.findall(r"[a-z]+", _sanitize(event_text, ticker).lower())
        if len(word) > 3 and word not in {"about", "after", "before", "from", "with", "this", "that"}
    }
    finding_by_id = {finding["id"]: finding for finding in findings}
    for point in output.points:
        cited_text = " ".join(finding_by_id[finding_id]["plain_summary"] for finding_id in point.findings if finding_id in finding_by_id).lower()
        point_terms = set(re.findall(r"[a-z]+", (point.title + " " + point.explanation).lower()))
        if (event_terms & point_terms) - set(re.findall(r"[a-z]+", cited_text)):
            errors.append(f"point {point.title!r} uses the user's event as cited evidence")
    if errors:
        raise ValueError("; ".join(errors))
    return output


def synthesize_verdict(
    query: str,
    parsed: dict,
    cards: dict[str, CardOutput],
    aggregate,
    precedents: list[dict] | None = None,
) -> tuple[VerdictOutput, bool]:
    """Create the overview from ten plain findings, or a deterministic fallback."""
    del precedents  # No precedent data is sent into the overview language model.
    config = get_settings()
    ticker = str(parsed.get("ticker", ""))
    references = _build_references(cards)
    findings = _plain_findings(cards, ticker)
    if not config.llm_api_key:
        return _build_fallback(query, parsed, cards, aggregate, references), False

    horizon = int(parsed.get("horizon_days", 20) or 20)
    prompt = {
        "question": _sanitize(query, ticker),
        "company": company_name(ticker),
        "event": (
            _sanitize(str(parsed.get("event_type", "company event")), ticker)
        ),
        "findings": findings,
    }
    system_prompt = SYSTEM_PROMPT.replace("{horizon}", str(horizon))

    for attempt in range(2):
        started = time.monotonic()
        parsed_output, raw, used_fallback_model = json_completion(
            system_prompt=system_prompt,
            user_prompt=json.dumps(prompt, ensure_ascii=False),
            output_model=SynthesisOutput,
            max_tokens_override=2000,
            max_attempts=1,
        )
        if parsed_output is None:
            logger.warning("Overview generation attempt %d failed: %s", attempt + 1, str(raw)[:240])
            continue
        try:
            cleaned = _validate_and_clean(
                parsed_output,
                findings,
                ticker,
                str(parsed.get("event_type", "")),
            )
            result = _assemble_verdict(
                cleaned,
                ticker=ticker,
                aggregate=aggregate,
                references=references,
                is_fallback=False,
                model_used=(config.llm_fallback_model or config.llm_model) if used_fallback_model else config.llm_model,
                is_fallback_model=used_fallback_model,
            )
            logger.info("Overview generated in %dms", int((time.monotonic() - started) * 1000))
            return result, True
        except ValueError as exc:
            logger.warning("Overview validation attempt %d failed: %s", attempt + 1, exc)

    logger.warning("Overview generation failed validation twice; using plain finding summaries")
    return _build_fallback(query, parsed, cards, aggregate, references), False
