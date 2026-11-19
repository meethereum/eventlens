"""Display names for the covered companies. Symbols stay inside backend code."""

COMPANY_NAMES = {
    "NVDA": "Nvidia",
    "INTC": "Intel",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GM": "General Motors",
    "SBUX": "Starbucks",
    "AMZN": "Amazon",
    "DIS": "Disney",
    "BA": "Boeing",
    "RTX": "Raytheon",
    "XOM": "ExxonMobil",
    "CVX": "Chevron",
    "JPM": "JPMorgan Chase",
    "SCHW": "Charles Schwab",
    "UNH": "UnitedHealth Group",
}


def company_name(symbol: str) -> str:
    """Return a readable covered company name, never the stock symbol."""
    return COMPANY_NAMES.get(symbol.upper(), "the company")
