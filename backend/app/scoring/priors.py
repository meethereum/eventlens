"""
Load exposure priors from config/exposure_priors.yaml.
Returns w_prior for a given card × ticker combination.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml

CONFIG_PATH = Path(os.environ.get("CONFIG_DIR", str(Path(__file__).parent.parent.parent / "config"))) / "exposure_priors.yaml"

# Card-id → YAML section key
_CARD_SECTION = {
    "C1": "usd",
    "C2": "rates",
    "C3": "oil",
    "C7": "geopolitics",
}

_CARD_DEFAULT_KEY = {
    "C1": "C1_usd",
    "C2": "C2_rates",
    "C3": "C3_oil",
    "C4": "C4_market",
    "C7": "C7_geopolitics",
}


@lru_cache(maxsize=1)
def _load() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_prior(card_id: str, ticker: str) -> float:
    """
    Return w_prior for the given card and ticker.
    Falls back to defaults section, then 0.3.
    """
    cfg = _load()
    section_key = _CARD_SECTION.get(card_id)
    if section_key:
        section = cfg.get(section_key, {})
        if ticker.upper() in section:
            return float(section[ticker.upper()])

    defaults = cfg.get("defaults", {})
    default_key = _CARD_DEFAULT_KEY.get(card_id)
    if default_key and default_key in defaults:
        return float(defaults[default_key])

    return 0.3
