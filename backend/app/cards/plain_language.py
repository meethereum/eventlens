"""Deterministic, plain-language findings for the ten evidence factors."""
from __future__ import annotations

import re
from typing import Any

from app.core.company_names import COMPANY_NAMES, company_name
from app.core.models import CardOutput

FACTOR_TITLES = {
    "C1": "United States dollar strength",
    "C2": "Interest rates and inflation",
    "C3": "Oil prices",
    "C4": "Market mood",
    "C5": "Compared with its industry",
    "C6": "Links to other industries",
    "C7": "World tension and policy risk",
    "C8": "Financial strength",
    "C9": "Sales and profit trend",
    "C10": "Price and valuation",
}

# Tickers and technical series names used only to translate source metrics.
_PROXY_NAMES = {
    "SMH": "chip makers",
    "TSM": "Taiwan Semiconductor Manufacturing",
    "CRWD": "cybersecurity companies",
    "SPR": "aircraft parts makers",
    "XLE": "energy companies",
    "XLY": "consumer goods companies",
    "XLI": "industrial companies",
    "KRE": "regional banks",
    "ITA": "defense companies",
    "XLY_2": "consumer goods companies",
}


def _value(card: CardOutput, *needles: str) -> Any | None:
    for metric in card.metrics:
        name = metric.name.lower()
        if all(needle.lower() in name for needle in needles):
            if any(_warning_matches(warning, needles) for warning in card.warnings):
                return None
            return metric.value
    return None


def _warning_matches(warning: str, needles: tuple[str, ...] | list[str]) -> bool:
    text = warning.lower()
    return "insufficient" in text and any(needle.lower() in text for needle in needles)


def _number(value: Any, decimals: int = 2) -> str | None:
    if value is None or isinstance(value, str):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return f"{number:.{decimals}f}".rstrip("0").rstrip(".")


def _signed_percent(value: Any) -> str | None:
    number = _number(value, 1)
    if number is None:
        return None
    return f"{number}%" if number.startswith("-") else f"{number}%"


def _metric_is_available(card: CardOutput, *needles: str) -> bool:
    return _value(card, *needles) is not None


def _plain_summary(card: CardOutput, ticker: str) -> str:
    company = company_name(ticker)
    if card.id == "C1":
        recent = _signed_percent(_value(card, "20d change"))
        longer = _signed_percent(_value(card, "60d change"))
        if recent and longer:
            return f"The United States dollar changed {recent} over the past 20 trading days and {longer} over the past 60 trading days."
        if recent:
            return f"The United States dollar changed {recent} over the past 20 trading days."
    elif card.id == "C2":
        rate = _number(_value(card, "10y yield"))
        change = _number(_value(card, "20d change"), 1)
        inflation = _number(_value(card, "CPI YoY"), 1)
        parts = []
        if rate is not None:
            parts.append(f"The long term United States government borrowing rate is {rate}%.")
        if change is not None:
            parts.append(f"It changed by {change} basis points over 20 trading days.")
        if inflation is not None:
            parts.append(f"Prices rose {inflation}% compared with a year ago.")
        if rate is not None and change is not None and inflation is not None:
            return f"The long term United States government borrowing rate is {rate}%, after changing by {change} basis points over 20 trading days. Prices rose {inflation}% compared with a year ago."
        if parts:
            return " ".join(parts[:2])
    elif card.id == "C3":
        price = _number(_value(card, "WTI price"))
        recent = _signed_percent(_value(card, "20d change"))
        longer = _signed_percent(_value(card, "60d change"))
        first = f"Oil costs ${price} per barrel." if price is not None else "Oil price data is not available."
        if recent and longer:
            return f"{first} The price changed {recent} over 20 trading days and {longer} over 60 trading days."
        changes = [value for value in (recent, longer) if value]
        if changes:
            period = "20" if recent else "60"
            return f"{first} The price changed {changes[0]} over {period} trading days."
        return first
    elif card.id == "C4":
        recent = _signed_percent(_value(card, "SPY 20d"))
        longer = _signed_percent(_value(card, "SPY 60d"))
        volatility = _number(_value(card, "VIX level"), 1)
        returns = []
        if recent:
            returns.append(f"{recent} over 20 trading days")
        if longer:
            returns.append(f"{longer} over 60 trading days")
        first = f"The broad share market changed {' and '.join(returns)}." if returns else "Broad share market readings are not available."
        return f"{first} The market volatility reading is {volatility}." if volatility is not None else first
    elif card.id == "C5":
        values = []
        for metric in card.metrics:
            name = metric.name.lower()
            if name.endswith(" 20d") and metric.value is not None:
                value = _signed_percent(metric.value)
                if not value:
                    continue
                if name.startswith(ticker.lower()):
                    label = company
                elif name.startswith("spy"):
                    label = "the wider United States market"
                else:
                    label = "the industry"
                values.append((label, value))
        company_move = next((value for label, value in values if label == company), None)
        industry_move = next((value for label, value in values if label == "the industry"), None)
        market_move = next((value for label, value in values if label == "the wider United States market"), None)
        if company_move and industry_move:
            suffix = f" The wider United States market changed {market_move}." if market_move else ""
            return f"{company}'s share price changed {company_move} over 20 trading days, while its industry changed {industry_move}.{suffix}"
    elif card.id == "C6":
        linked = []
        for metric in card.metrics:
            match = re.match(r"([A-Z0-9_]+)\s+20d$", metric.name)
            if match and metric.value is not None:
                proxy = match.group(1)
                name = _PROXY_NAMES.get(proxy, COMPANY_NAMES.get(proxy, "related companies"))
                value = _signed_percent(metric.value)
                if value and not any(proxy.lower() in warning.lower() for warning in card.warnings):
                    linked.append(f"{name} changed {value}")
        if linked:
            return f"The selected business links include {linked[0]} over 20 trading days. These links are curated and do not show that one company caused another company's results."
        return "No measured business links are available for this company."
    elif card.id == "C7":
        level = _number(_value(card, "GPR level"), 1)
        change = _number(_value(card, "GPR 3m change"), 1)
        policy = _number(_value(card, "US Policy Uncertainty"), 1)
        parts = []
        if level is not None:
            parts.append(f"A measure of world tension is {level}.")
        if change is not None:
            parts.append(f"It changed by {change} over three months.")
        if policy is not None:
            parts.append(f"A measure of uncertainty about United States policy is {policy}.")
        if level is not None and change is not None:
            second = f"It changed by {change} over three months."
            if policy is not None:
                second = f"It changed by {change} over three months, and a measure of United States policy uncertainty is {policy}."
            return f"A measure of world tension is {level}. {second}"
        return " ".join(parts[:2]) or "World tension readings are not available."
    elif card.id == "C8":
        current = _number(_value(card, "Current ratio"))
        debt = _number(_value(card, "Debt/Equity"))
        interest = _number(_value(card, "Interest coverage"))
        equity_assets = _number(_value(card, "Equity/Assets"), 1)
        margin = _number(_value(card, "Operating margin"), 1)
        if equity_assets is not None:
            first = f"Owners' funds make up {equity_assets}% of the company's assets."
            second = f"Profit from operations is {margin}% of revenue." if margin is not None else "The available data does not include operating profit compared with revenue."
            return f"{first} {second}"
        parts = []
        if current is not None:
            parts.append(f"For each dollar due soon, {company} has {current} dollars in short term assets.")
        if debt is not None:
            parts.append(f"Its debt is {debt} times its recorded owner value.")
        if interest is not None:
            parts.append(f"Its operating profit covers interest costs {interest} times.")
        if margin is not None:
            parts.append(f"Profit from operations is {margin}% of revenue.")
        return " ".join(parts[:2]) or "The available company filing does not contain enough figures for this check."
    elif card.id == "C9":
        revenue = _signed_percent(_value(card, "Revenue YoY"))
        profit = _signed_percent(_value(card, "Diluted EPS YoY"))
        margin = next((str(metric.value).lower() for metric in card.metrics if "gross margin trend" in metric.name.lower() and metric.value), None)
        first_parts = []
        if revenue:
            first_parts.append(f"Sales changed {revenue} compared with a year ago.")
        if profit:
            first_parts.append(f"Profit per share changed {profit} compared with a year ago.")
        if margin:
            first_parts.append(f"The share of sales left after direct costs is {margin}.")
        return " ".join(first_parts[:2]) or "Sales and profit figures are not available."
    elif card.id == "C10":
        multiple = _number(_value(card, "P/E TTM"), 1)
        position = _number(_value(card, "52-week range"), 0)
        ma50 = next((str(metric.value).lower() for metric in card.metrics if "50d ma trend" in metric.name.lower()), None)
        ma200 = next((str(metric.value).lower() for metric in card.metrics if "200d ma trend" in metric.name.lower()), None)
        parts = []
        if multiple is not None:
            parts.append(f"The share price is {multiple} times the latest yearly profit per share.")
        if position is not None:
            parts.append(f"It is at {position}% of its price range over the past year.")
        if ma50 and ma200:
            first = "above" if ma50 == "above" else "below"
            second = "above" if ma200 == "above" else "below"
            parts.append(f"The share price is {first} its average over 50 days and {second} its average over 200 days.")
        return " ".join(parts[:2]) or "Price and company profit figures are not available."
    return "No plain language finding is available for this factor yet."


def enrich_card(card: CardOutput, ticker: str) -> CardOutput:
    """Attach deterministic reader-facing fields without changing any scores."""
    title = FACTOR_TITLES.get(card.id, "Evidence finding")
    direction = {
        "tailwind": "for",
        "headwind": "against",
        "neutral": "neutral",
    }.get(str(card.label), "neutral")
    strength_value = abs(card.signal)
    strength = "strong" if strength_value >= 0.6 else "moderate" if strength_value >= 0.3 else "slight"
    summary = _plain_summary(card, ticker)
    return card.model_copy(update={
        "plain_title": title,
        "plain_summary": _clean_plain_text(summary),
        "direction": direction,
        "strength": strength,
    })


def _clean_plain_text(text: str) -> str:
    """Keep generated findings free of symbols, abbreviations, and dash marks."""
    for symbol in sorted(COMPANY_NAMES, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(symbol)}\b", company_name(symbol), text, flags=re.IGNORECASE)
    text = re.sub(r"\bUS\b", "United States", text)
    replacements = {
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
        "SVB": "a large bank",
        "TTM": "the latest year",
        "CET1": "bank owners' funds",
        "S&P": "United States share market",
    }
    for token, replacement in replacements.items():
        text = re.sub(rf"\b{re.escape(token)}\b", replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\b[A-Z]{2,}\b", lambda match: match.group(0).lower(), text)
    text = re.sub(r"(?<!\w)[−-](?=\d)", "minus ", text)
    text = re.sub(r"[‐‑‒–—―]+", ",", text)
    text = re.sub(r"(?<!\w)[−-](?!\d)", ",", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
