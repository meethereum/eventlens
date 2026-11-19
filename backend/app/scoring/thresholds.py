"""
Load financial thresholds from config/thresholds.yaml.
Used by C8, C9, C10 to convert raw values into band scores.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml

_CONFIG_DIR = Path(os.environ.get(
    "CONFIG_DIR",
    str(Path(__file__).parent.parent.parent / "config"),
))
if not (_CONFIG_DIR / "thresholds.yaml").exists():
    _CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"
CONFIG_PATH = _CONFIG_DIR / "thresholds.yaml"


@lru_cache(maxsize=1)
def _load() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_bank_tickers() -> set[str]:
    """Return the set of tickers that use bank/broker financial-health rules."""
    cfg = _load()
    return set(cfg.get("bank_tickers", []))


def is_bank(ticker: str) -> bool:
    return ticker.upper() in get_bank_tickers()


def get_sector_for_ticker(ticker: str) -> str | None:
    """Return the sector name for a ticker from sector_map, or None."""
    try:
        sector_map_path = _CONFIG_DIR / "sector_map.yaml"
        with open(sector_map_path) as f:
            sm = yaml.safe_load(f)
        info = sm.get("ticker_sector", {}).get(ticker.upper())
        return info["sector"] if info else None
    except Exception:
        return None


def get_threshold(metric: str, ticker: str | None = None) -> dict:
    """
    Return threshold dict for a metric, applying sector overrides if applicable.
    """
    cfg = _load()
    base = cfg.get(metric, {})

    if ticker:
        sector = get_sector_for_ticker(ticker)
        overrides = cfg.get("sector_overrides", {})
        if sector and sector in overrides and metric in overrides[sector]:
            base = {**base, **overrides[sector][metric]}

    return base


def overview_confidence(coverage: float, agreement: float) -> str:
    """Return a confidence label using configured coverage and agreement cutoffs."""
    cfg = _load().get("overview_confidence", {})
    high = cfg.get("high", {})
    medium = cfg.get("medium", {})
    if (
        coverage >= high.get("minimum_coverage", 0.8)
        and agreement >= high.get("minimum_agreement", 0.55)
    ):
        return "High"
    if (
        coverage >= medium.get("minimum_coverage", 0.5)
        and agreement >= medium.get("minimum_agreement", 0.3)
    ):
        return "Medium"
    return "Low"


def band_score(value: float | None, strong: float, weak: float, inverted: bool = False) -> float:
    """
    Convert a value to a score in [-1, 1] based on bands.
    - If not inverted: value >= strong → +1, value <= weak → -1, linear between.
    - If inverted (e.g. P/E percentile where low is good): value <= strong → +1, value >= weak → -1.
    """
    if value is None or value != value:  # NaN check
        return 0.0

    if inverted:
        # Low is good (e.g. P/E percentile)
        if value <= strong:
            return 1.0
        if value >= weak:
            return -1.0
        # Linear interpolation: strong → +1, weak → -1
        return float((weak - value) / (weak - strong)) if weak != strong else 0.0
    else:
        # High is good (e.g. interest coverage)
        if value >= strong:
            return 1.0
        if value <= weak:
            return -1.0
        # Linear interpolation: weak → -1, strong → +1
        return float((value - weak) / (strong - weak)) if strong != weak else 0.0
