"""
Card registry — maps card_id → (title, fetch_fn).
Adding a card here is all that's needed to include it in the pipeline.
"""
from __future__ import annotations

from typing import Callable

from app.core.models import CardOutput

# Import card modules
from app.cards import (
    c1_usd, c2_rates, c3_oil, c4_market,
    c5_sector, c6_dependency, c7_geopolitics,
    c8_financial, c9_earnings, c10_valuation,
)

CardFn = Callable[[str, str], CardOutput]  # (ticker, as_of) -> CardOutput

# Ordered list — determines fetch order in the pipeline
CARDS: list[tuple[str, str, CardFn]] = [
    ("C1",  c1_usd.CARD_TITLE,         c1_usd.fetch),
    ("C2",  c2_rates.CARD_TITLE,       c2_rates.fetch),
    ("C3",  c3_oil.CARD_TITLE,         c3_oil.fetch),
    ("C4",  c4_market.CARD_TITLE,      c4_market.fetch),
    ("C5",  c5_sector.CARD_TITLE,      c5_sector.fetch),
    ("C6",  c6_dependency.CARD_TITLE,   c6_dependency.fetch),
    ("C7",  c7_geopolitics.CARD_TITLE,  c7_geopolitics.fetch),
    ("C8",  c8_financial.CARD_TITLE,    c8_financial.fetch),
    ("C9",  c9_earnings.CARD_TITLE,     c9_earnings.fetch),
    ("C10", c10_valuation.CARD_TITLE,   c10_valuation.fetch),
]

CARD_IDS   = [c[0] for c in CARDS]
CARD_TITLES = {c[0]: c[1] for c in CARDS}
