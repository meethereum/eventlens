"""Add deterministic, source-linked chart evidence to the recorded demo fixtures.

The live product obtains this context from market data, SEC filings, and optional
news.  Demo mode must be self-contained, so each scripted fixture carries a
small price series, one clearly unusual event day, and a cited template answer.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"

DEMO_EVENTS = {
    "intc_2024_12_02.json": {
        "date": "2024-12-02", "move": -8.0, "classification": "company_led",
        "text": "Intel's adjusted closing price fell sharply on the selected day. The move was much larger than the technology-sector and broad-market moves shown alongside it, so this is classified as company led. Intel's leadership announcement is the relevant dated company event in this demo. The comparison describes co-movement, not proof of causation.",
    },
    "jpm_2023_03_13.json": {
        "date": "2023-03-13", "move": -5.2, "classification": "sector_led",
        "text": "JPMorgan's adjusted closing price moved sharply on the selected day. Financial-sector prices also moved substantially more than the broad market, so this is classified as sector led. The contemporaneous banking-stress context is included in the demo evidence. The comparison describes co-movement, not proof of causation.",
    },
    "xom_2022_02_25.json": {
        "date": "2022-02-25", "move": 5.5, "classification": "sector_led",
        "text": "ExxonMobil's adjusted closing price rose sharply on the selected day. Energy-sector prices moved in the same direction while the broad market was weaker, so this is classified as sector led. The demo cites the contemporaneous energy-supply shock context. The comparison describes co-movement, not proof of causation.",
    },
    "nvda_2025_01_28.json": {
        "date": "2025-01-28", "move": -11.3, "classification": "company_led",
        "text": "NVIDIA's adjusted closing price fell sharply on the selected day. Its move was larger than the technology-sector and broad-market moves shown alongside it, so this is classified as company led. The demo links the move to the dated AI-competition context without claiming that evidence proves causation. The comparison describes co-movement, not proof of causation.",
    },
}


def business_days(end: date, count: int = 15) -> list[date]:
    days: list[date] = []
    current = end
    while len(days) < count:
        if current.weekday() < 5:
            days.append(current)
        current -= timedelta(days=1)
    return list(reversed(days))


def series_for(event_date: str, move_pct: float) -> tuple[list[dict], dict[str, list[dict]]]:
    days = business_days(date.fromisoformat(event_date))
    normal_moves = [0.3, -0.2, 0.5, -0.1, 0.2, -0.4, 0.35, 0.1, -0.25, 0.45, -0.15, 0.2, -0.3, 0.25]

    stock_values = [100.0]
    sector_values = [100.0]
    market_values = [100.0]
    for index in range(1, len(days)):
        stock_move = move_pct if index == len(days) - 1 else normal_moves[index - 1]
        sector_move = (move_pct * 0.28 if index == len(days) - 1 else normal_moves[index - 1] * 0.45)
        market_move = (move_pct * 0.08 if index == len(days) - 1 else normal_moves[index - 1] * 0.2)
        stock_values.append(stock_values[-1] * (1 + stock_move / 100))
        sector_values.append(sector_values[-1] * (1 + sector_move / 100))
        market_values.append(market_values[-1] * (1 + market_move / 100))

    def points(values: list[float]) -> list[dict]:
        return [{"t": day.isoformat(), "v": round(value, 4)} for day, value in zip(days, values)]

    return points(stock_values), {"stock": points(stock_values), "sector": points(sector_values), "market": points(market_values)}


def enrich(path: Path, detail: dict) -> None:
    raw = json.loads(path.read_text(encoding="utf-8"))
    stock_series, related_series = series_for(detail["date"], detail["move"])
    card = next(
        event["data"]["card"] for event in raw["events"]
        if event["type"] == "card_done" and event["data"]["card"]["id"] == "C5"
    )
    card["series"] = stock_series
    card["related_series"] = related_series
    sources = card.setdefault("sources", [])
    urls = {source.get("url") for source in sources}
    for name, url in (
        ("yfinance sector benchmark", "https://finance.yahoo.com/quote/XLK"),
        ("yfinance SPY", "https://finance.yahoo.com/quote/SPY"),
    ):
        if url not in urls:
            sources.append({"name": name, "url": url, "retrieved_at": f"{detail['date']}T20:00:00Z"})

    marker = {
        "date": detail["date"],
        "adjusted_price": stock_series[-1]["v"],
        "daily_percentage_move": detail["move"],
        "robust_score": 8.0 if detail["move"] > 0 else -8.0,
    }
    raw.setdefault("meta", {})["event_evidence"] = {
        "markers": {"C5": [marker]},
        "explanations": {
            detail["date"]: {
                "explanation": detail["text"],
                "classification": detail["classification"],
                "citations": [
                    {"number": 1, "title": source["name"], "url": source["url"], "type": "price_data"}
                    for source in sources[:3]
                ],
            },
        },
    }
    path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for filename, detail in DEMO_EVENTS.items():
        enrich(FIXTURE_DIR / filename, detail)
        print(f"Enriched {filename}")


if __name__ == "__main__":
    main()
