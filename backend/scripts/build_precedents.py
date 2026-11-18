#!/usr/bin/env python3
"""Build source-linked precedent outcomes from SEC filings and adjusted closes."""
from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from app.cards.c5_sector import _get_sector_etf
from app.core.config import get_settings
from app.core.edgar_client import get_cik, _headers_data
from app.core.yf_client import fetch_prices
from scripts.validate_precedents import DATA_PATH, validate_dataset

TICKERS = (
    "NVDA", "INTC", "AAPL", "MSFT", "GM", "SBUX", "AMZN", "DIS",
    "BA", "RTX", "XOM", "CVX", "JPM", "SCHW", "UNH",
)
START_DATE = date(2015, 1, 1)
END_DATE = date(2025, 12, 31)
TARGETS_PER_TICKER = 8
PRICE_LOOKBACK_DAYS = 4_500


def _submission_payload(ticker: str) -> dict[str, Any]:
    cik = get_cik(ticker)
    if not cik:
        raise ValueError(f"SEC CIK was not found for {ticker}")
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    with httpx.Client(timeout=30, headers=_headers_data()) as client:
        time.sleep(0.2)
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()

        recent = payload["filings"]["recent"]
        rows = {key: list(values) for key, values in recent.items()}
        for older in payload.get("filings", {}).get("files", []):
            first = older.get("filingFrom", "")
            last = older.get("filingTo", "")
            if not first or not last or last < START_DATE.isoformat() or first > END_DATE.isoformat():
                continue
            time.sleep(0.2)
            older_response = client.get(f"https://data.sec.gov/submissions/{older['name']}")
            older_response.raise_for_status()
            archived = older_response.json()
            for key, values in archived.items():
                rows.setdefault(key, []).extend(values)
    return rows


def _event_details(items: str) -> tuple[str, str, str]:
    item_set = {part.strip() for part in (items or "").split(",")}
    if "2.02" in item_set:
        return (
            "earnings",
            "Financial results or outlook update",
            "The company reported financial results or an update to its outlook in a current filing.",
        )
    if "5.02" in item_set:
        return (
            "leadership",
            "Leadership or governance change",
            "The company reported a leadership or governance change in a current filing.",
        )
    if item_set.intersection({"1.01", "2.01", "2.03", "2.04"}):
        return (
            "operational",
            "Material business or operating update",
            "The company disclosed a material business or operating update in a current filing.",
        )
    return (
        "company_event",
        "Material company update",
        "The company disclosed a material update in a current filing.",
    )


def _filing_candidates(ticker: str) -> list[dict[str, Any]]:
    cik = get_cik(ticker)
    if not cik:
        raise ValueError(f"SEC CIK was not found for {ticker}")
    submissions = _submission_payload(ticker)
    candidates = []
    for index, form in enumerate(submissions.get("form", [])):
        if form != "8-K":
            continue
        filed = submissions["filingDate"][index]
        event_date = date.fromisoformat(filed)
        document = submissions.get("primaryDocument", [""] * (index + 1))[index]
        accession = submissions.get("accessionNumber", [""] * (index + 1))[index]
        if not START_DATE <= event_date <= END_DATE or not document or not accession:
            continue
        items = submissions.get("items", [""] * (index + 1))[index] or ""
        category, event_type, summary = _event_details(items)
        accession_path = accession.replace("-", "")
        candidates.append({
            "id": f"{ticker.lower()}-{accession_path}",
            "event_date": event_date,
            "ticker": ticker,
            "category": category,
            "event_type": event_type,
            "summary": summary,
            "items": items,
            "source": {
                "title": f"SEC Form 8-K filed {filed} (Items {items or 'not specified'})",
                "url": (
                    f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                    f"{accession_path}/{document}"
                ),
            },
        })
    return candidates


def _choose_events(candidates: list[dict[str, Any]], ticker: str) -> list[dict[str, Any]]:
    unique_by_year: dict[int, list[dict[str, Any]]] = {}
    for event in candidates:
        unique_by_year.setdefault(event["event_date"].year, []).append(event)
    for events in unique_by_year.values():
        events.sort(key=lambda item: (item["event_date"], item["id"]))

    targets = [
        round(2015 + index * (2025 - 2015) / (TARGETS_PER_TICKER - 1))
        for index in range(TARGETS_PER_TICKER)
    ]
    chosen: list[dict[str, Any]] = []
    used_years: set[int] = set()
    used_categories: set[str] = set()
    for target_year in targets:
        available_years = [year for year in unique_by_year if year not in used_years]
        if not available_years:
            break
        year = min(available_years, key=lambda value: (abs(value - target_year), value))
        options = unique_by_year[year]
        event = next(
            (row for row in options if row["category"] not in used_categories),
            options[0],
        )
        chosen.append(event)
        used_years.add(year)
        used_categories.add(event["category"])

    if len(chosen) < TARGETS_PER_TICKER:
        remaining = sorted(
            (row for row in candidates if row["id"] not in {item["id"] for item in chosen}),
            key=lambda row: (row["event_date"], row["id"]),
        )
        chosen.extend(remaining[:TARGETS_PER_TICKER - len(chosen)])
    if len(chosen) < TARGETS_PER_TICKER:
        raise ValueError(
            f"{ticker} has only {len(chosen)} eligible SEC 8-K events in 2015–2025; "
            f"{TARGETS_PER_TICKER} are required"
        )
    return sorted(chosen[:TARGETS_PER_TICKER], key=lambda item: (item["event_date"], item["id"]))


def _normalized_outcomes(
    event: dict[str, Any],
    prices: dict[str, pd.Series],
) -> dict[str, Any] | None:
    ticker = event["ticker"]
    sector_etf, sector_name = _get_sector_etf(ticker)
    aligned = pd.concat(
        {
            "stock": prices[ticker],
            "sector": prices[sector_etf],
            "spy": prices["SPY"],
        },
        axis=1,
        join="inner",
    ).dropna().sort_index()
    eligible = aligned.index >= pd.Timestamp(event["event_date"])
    positions = [index for index, keep in enumerate(eligible) if keep]
    if not positions:
        return None
    start = positions[0]
    window = aligned.iloc[start:start + 61]
    if len(window) != 61:
        return None

    normalized: dict[str, list[dict[str, Any]]] = {}
    returns: dict[str, dict[str, float]] = {}
    for entity in ("stock", "sector", "spy"):
        anchor = float(window[entity].iloc[0])
        points = [
            {
                "day": day,
                "date": timestamp.date().isoformat(),
                "value": round(float(value) / anchor * 100, 6),
            }
            for day, (timestamp, value) in enumerate(window[entity].items())
        ]
        normalized[entity] = points
        returns[entity] = {
            f"d{days}": round(points[days]["value"] - 100, 4)
            for days in (5, 20, 60)
        }

    prior = aligned.loc[aligned.index < pd.Timestamp(event["event_date"]), "spy"].tail(21)
    if len(prior) < 2:
        market_mood = "mixed"
    else:
        prior_move = (float(prior.iloc[-1]) / float(prior.iloc[0]) - 1) * 100
        market_mood = "risk_off" if prior_move <= -2 else "risk_on" if prior_move >= 2 else "mixed"

    return {
        "sector": sector_name.lower(),
        "sector_etf": sector_etf,
        "market_mood": market_mood,
        "outcomes": {"returns": returns, "series": normalized},
    }


def build_records() -> list[dict[str, Any]]:
    candidates: dict[str, list[dict[str, Any]]] = {}
    for ticker in TICKERS:
        candidates[ticker] = _choose_events(_filing_candidates(ticker), ticker)

    tickers = set(TICKERS) | {"SPY"}
    tickers.update(_get_sector_etf(ticker)[0] for ticker in TICKERS)
    prices = {
        ticker: fetch_prices(
            ticker,
            as_of=date.today().isoformat(),
            lookback_days=PRICE_LOOKBACK_DAYS,
        )
        for ticker in sorted(tickers)
    }

    records: list[dict[str, Any]] = []
    for ticker in TICKERS:
        for event in candidates[ticker]:
            outcomes = _normalized_outcomes(event, prices)
            if outcomes is None:
                continue
            records.append({
                "id": event["id"],
                "event_date": event["event_date"].isoformat(),
                "ticker": ticker,
                "sector": outcomes["sector"],
                "sector_etf": outcomes["sector_etf"],
                "event_type": event["event_type"],
                "category": event["category"],
                "market_mood": outcomes["market_mood"],
                "summary": event["summary"],
                "source": event["source"],
                "outcomes": outcomes["outcomes"],
            })

    if len(records) < 100:
        counts: dict[str, int] = {}
        for row in records:
            counts[row["ticker"]] = counts.get(row["ticker"], 0) + 1
        raise ValueError(f"Only {len(records)} complete outcomes were built; per-ticker counts: {counts}")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EventLens historical precedents.")
    parser.add_argument("--output", type=Path, default=DATA_PATH)
    args = parser.parse_args()
    if not get_settings().sec_user_agent or "example.com" in get_settings().sec_user_agent:
        raise ValueError("Set SEC_USER_AGENT to a real contact value before querying SEC EDGAR.")

    records = build_records()
    # Each source link is constructed from the SEC submissions response that
    # supplied the filing. Structural validation happens before the atomic
    # write; the optional --check-urls validator remains available for a
    # deliberately paced exhaustive HTTP verification pass.
    validate_dataset(records, date.today())
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(f"Wrote {len(records)} validated precedents to {args.output}")


if __name__ == "__main__":
    main()
