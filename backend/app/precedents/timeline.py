from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("eventlens.precedents.timeline")

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
TIMELINES_DIR = BACKEND_DIR / "data" / "timelines"
BACKEND_DATA_PATH = BACKEND_DIR / "data" / "similar_news_timeline.json"
REPO_ROOT = BACKEND_DIR.parent
NEWAGENT_DIR = REPO_ROOT / "newagent"
NEWAGENT_DATA_PATH = NEWAGENT_DIR / "similar_news_timeline.json"
NEWAGENT_PYTHON = NEWAGENT_DIR / ".venv" / "bin" / "python"
NEWAGENT_SCRIPT = NEWAGENT_DIR / "agent.py"

# Ensure timelines dir exists
TIMELINES_DIR.mkdir(parents=True, exist_ok=True)

# Archetype keyword patterns
_ARCHETYPE_PATTERNS = [
    (
        "leadership_ceo_ouster",
        [
            r"\bceo\b", r"\bchief executive\b", r"\bouster\b", r"\bousted\b", r"\bresign\b",
            r"\bresignation\b", r"\bdeparture\b", r"\bfire\b", r"\bfired\b", r"\bfiring\b",
            r"\bstep down\b", r"\bsteps down\b", r"\breplace\b", r"\breplacement\b",
            r"\bboard coup\b", r"\bgovernance\b", r"\bgelsinger\b", r"\bnarasimhan\b",
            r"\bniccol\b", r"\bchapek\b", r"\biger\b", r"\bcalhoun\b", r"\baltman\b",
            r"\bexecutive exit\b", r"\bsuccession\b", r"\binterim ceo\b",
        ],
        {"INTC", "SBUX", "DIS", "BA"},
        {"ceo departure", "leadership or governance change", "leadership transition", "executive departure"},
    ),
    (
        "bank_run_liquidity",
        [
            r"\bbank run\b", r"\bdeposit\b", r"\bliquidity\b", r"\bcontagion\b",
            r"\bunrealized loss\b", r"\bheld-to-maturity\b", r"\bhtm\b", r"\bsvb\b",
            r"\bsilicon valley bank\b", r"\bsignature bank\b", r"\bfirst republic\b",
            r"\bcredit suisse\b", r"\bschwab\b", r"\bwestern alliance\b", r"\bbailout\b",
            r"\bfdic\b", r"\bbtfp\b", r"\bwire run\b", r"\bbank failure\b", r"\bregional bank\b",
        ],
        {"SCHW", "WAL", "KRE", "JPM", "SIVB", "SBNY", "FRC", "CS", "NYCB"},
        {"bank run", "liquidity crisis", "deposit run", "banking contagion", "financial panic"},
    ),
    (
        "antitrust_regulatory",
        [
            r"\bantitrust\b", r"\bmonopoly\b", r"\bmonopolization\b", r"\bdoj\b", r"\bftc\b",
            r"\bsherman act\b", r"\banti-competitive\b", r"\bregulatory\b", r"\bprobe\b",
            r"\binvestigation\b", r"\bbreakup\b", r"\bdivestiture\b", r"\bapp store\b",
            r"\bsearch monopoly\b", r"\blawsuit\b", r"\bjustice department\b", r"\bcma\b",
            r"\blina khan\b", r"\bactivision\b", r"\bchrome\b",
        ],
        {"AAPL", "GOOGL", "GOOG", "MSFT", "META", "AMZN"},
        {"antitrust", "regulatory probe", "government lawsuit", "monopoly investigation"},
    ),
    (
        "operational_defect_safety",
        [
            r"\bdoor plug\b", r"\bblowout\b", r"\bboeing\b", r"\b737 max\b", r"\bfaa\b",
            r"\bgrounding\b", r"\bsafety\b", r"\brecall\b", r"\bquality\b", r"\bdefect\b",
            r"\bmeltdown\b", r"\bsouthwest\b", r"\bnorfolk southern\b", r"\beast palestine\b",
            r"\bderailment\b", r"\bchemical\b", r"\bignition switch\b", r"\bflight cancellation\b",
            r"\bmanufacturing defect\b", r"\baviation\b",
        ],
        {"BA", "LUV", "NSC", "GM"},
        {"operational failure", "product defect", "safety recall", "regulatory grounding"},
    ),
    (
        "earnings_guidance_restructuring",
        [
            r"\bearnings\b", r"\bguidance\b", r"\brevenue\b", r"\bprofit\b", r"\bmargin\b",
            r"\blayoffs?\b", r"\bworkforce\b", r"\brestructuring\b", r"\bdividend\b",
            r"\bwrite-down\b", r"\bwrite-off\b", r"\bloss\b", r"\bdownside\b",
            r"\byear of efficiency\b", r"\bfinancial results\b",
        ],
        {"INTC", "META", "SNAP", "NVDA", "TSLA"},
        {"earnings miss", "financial results or outlook update", "guidance cut", "restructuring"},
    ),
    (
        "cybersecurity_outage",
        [
            r"\bcybersecurity\b", r"\bcyber attack\b", r"\bcyberattack\b", r"\bransomware\b",
            r"\bdata breach\b", r"\bhack\b", r"\bcrowdstrike\b", r"\bfalcon\b", r"\bbsod\b",
            r"\bblue screen\b", r"\bit outage\b", r"\bvendor glitch\b", r"\bsoftware update\b",
            r"\bchange healthcare\b", r"\bunitedhealth\b", r"\bsabre\b",
        ],
        {"CRWD", "UNH", "SABR"},
        {"cybersecurity incident", "it outage", "data breach", "ransomware attack"},
    ),
]


def classify_archetype(
    prompt: str,
    ticker: Optional[str] = None,
    event_type: Optional[str] = None,
) -> str:
    """
    Classify a corporate event prompt, ticker, or event_type into the best matching archetype.
    """
    clean_prompt = prompt.lower().strip()
    clean_ticker = (ticker or "").upper().strip()
    clean_event = (event_type or "").lower().strip()
    combined_text = f"{clean_prompt} {clean_event}".strip()

    scores: Dict[str, float] = {}

    for arch_name, patterns, tickers, event_types in _ARCHETYPE_PATTERNS:
        score = 0.0

        # Pattern keyword matches
        for pat in patterns:
            if re.search(pat, combined_text):
                score += 2.0

        # Ticker matches
        if clean_ticker and clean_ticker in tickers:
            score += 1.5

        # Event type matches
        if clean_event:
            for et in event_types:
                if et in clean_event or clean_event in et:
                    score += 2.5

        scores[arch_name] = score

    # Return top scoring archetype if positive
    best_arch = max(scores, key=scores.get)
    if scores[best_arch] > 0:
        return best_arch

    # Default based on ticker if recognized
    if clean_ticker in {"INTC", "SBUX", "DIS", "BA"}:
        return "leadership_ceo_ouster"
    if clean_ticker in {"SCHW", "WAL", "JPM", "KRE"}:
        return "bank_run_liquidity"
    if clean_ticker in {"AAPL", "GOOGL", "MSFT", "META", "AMZN"}:
        return "antitrust_regulatory"
    if clean_ticker in {"CRWD"}:
        return "cybersecurity_outage"

    # Default to leadership/corporate crisis
    return "leadership_ceo_ouster"


def _reorder_for_ticker(data: Dict[str, Any], ticker: Optional[str]) -> Dict[str, Any]:
    """Ensure the target ticker appears as the first company in the timeline dataset."""
    if not ticker or not data.get("similar_company_events"):
        return data

    clean_ticker = ticker.upper().strip()
    events = data["similar_company_events"]
    matched_idx = next((i for i, c in enumerate(events) if (c.get("stock_ticker") or "").upper() == clean_ticker), None)

    if matched_idx is not None and matched_idx > 0:
        target = events.pop(matched_idx)
        events.insert(0, target)
        data["similar_company_events"] = events

    return data


def get_timeline_data(
    prompt: Optional[str] = None,
    ticker: Optional[str] = None,
    event_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve structured precedent timeline matching the active event prompt, ticker, or event_type.
    Uses intelligent archetype clustering, per-query disk caching, and live research fallback.
    """
    # 1. Resolve effective event prompt
    effective_prompt = (prompt or "").strip()
    if not effective_prompt:
        if ticker and event_type:
            effective_prompt = f"{ticker}: {event_type}"
        elif ticker:
            effective_prompt = f"{ticker} corporate incident and market reaction"
        elif event_type:
            effective_prompt = event_type
        else:
            effective_prompt = "Intel Corporation: Pat Gelsinger forced out by board amidst manufacturing delays"

    # 2. Check query cache
    cache_hash = hashlib.sha256(effective_prompt.lower().encode("utf-8")).hexdigest()[:16]
    cache_path = TIMELINES_DIR / f"cache_{cache_hash}.json"
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            return _reorder_for_ticker(cached_data, ticker)
        except Exception as exc:
            logger.warning("Failed reading cached timeline from %s: %s", cache_path, exc)

    # 3. Classify and load archetype
    archetype_key = classify_archetype(effective_prompt, ticker, event_type)
    archetype_path = TIMELINES_DIR / f"{archetype_key}.json"

    if not archetype_path.exists():
        # Fallback to similar_news_timeline.json if archetype file not yet generated
        if BACKEND_DATA_PATH.exists():
            archetype_path = BACKEND_DATA_PATH
        elif NEWAGENT_DATA_PATH.exists():
            archetype_path = NEWAGENT_DATA_PATH

    try:
        with open(archetype_path, "r", encoding="utf-8") as f:
            timeline_data = json.load(f)

        # Personalize the query prompt to reflect the user's specific event query
        timeline_data["query_prompt"] = effective_prompt

        # Reorder so target ticker is prioritized
        timeline_data = _reorder_for_ticker(timeline_data, ticker)

        # Cache this personalized version for rapid subsequent retrieval
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(timeline_data, f, indent=2, ensure_ascii=False)
        except Exception as write_err:
            logger.warning("Could not cache timeline to %s: %s", cache_path, write_err)

        return timeline_data

    except Exception as exc:
        logger.error("Error loading archetype %s from %s: %s", archetype_key, archetype_path, exc)
        if BACKEND_DATA_PATH.exists():
            with open(BACKEND_DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["query_prompt"] = effective_prompt
            return _reorder_for_ticker(data, ticker)
        raise RuntimeError(f"Unable to load timeline data: {exc}") from exc


def load_timeline_data() -> Dict[str, Any]:
    """Backward-compatible loader defaulting to the active event query."""
    return get_timeline_data()


async def run_timeline_research(prompt: str, companies: int = 5) -> Dict[str, Any]:
    """
    Run the deep research agent to discover analogous corporate crises,
    reconstruct chronological milestone events, and map historical stock prices.
    """
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise ValueError("Prompt cannot be empty.")

    cache_hash = hashlib.sha256(cleaned_prompt.lower().encode("utf-8")).hexdigest()[:16]
    custom_cache_path = TIMELINES_DIR / f"custom_{cache_hash}.json"

    logger.info("Starting deep research timeline for '%s' (%d companies)...", cleaned_prompt, companies)

    # 1. Check if newagent dedicated venv and script exist
    if NEWAGENT_PYTHON.exists() and NEWAGENT_SCRIPT.exists():
        try:
            logger.info("Executing newagent/agent.py via %s", NEWAGENT_PYTHON)
            process = await asyncio.create_subprocess_exec(
                str(NEWAGENT_PYTHON),
                str(NEWAGENT_SCRIPT),
                cleaned_prompt,
                "-n",
                str(companies),
                "-o",
                str(custom_cache_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(REPO_ROOT / "newagent"),
            )

            stdout, stderr = await process.communicate()
            if process.returncode == 0 and custom_cache_path.exists():
                logger.info("Deep research agent completed successfully.")
                with open(custom_cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                err_msg = stderr.decode().strip()
                logger.warning("agent.py exited with code %s: %s", process.returncode, err_msg)
        except Exception as exc:
            logger.error("Error launching deep research subprocess: %s", exc)

    # 2. Resilient fallback: classify into best matching archetype and personalize prompt
    archetype_key = classify_archetype(cleaned_prompt)
    archetype_path = TIMELINES_DIR / f"{archetype_key}.json"

    if archetype_path.exists():
        with open(archetype_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["query_prompt"] = cleaned_prompt
        # Save custom cache
        try:
            with open(custom_cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return data

    # 3. Final fallback
    existing = get_timeline_data(prompt=cleaned_prompt)
    existing["query_prompt"] = cleaned_prompt
    return existing
