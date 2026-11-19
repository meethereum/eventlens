#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from datetime import date
from pathlib import Path

import httpx
from pydantic import ValidationError

from app.core.config import get_settings
from app.precedents.schema import PrecedentRecord, SUPPORTED_TICKERS

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "precedents.json"


def validate_dataset(rows: list[dict], as_of: date, require_minimum: bool = True) -> list[PrecedentRecord]:
    records = []
    for row in rows:
        try:
            records.append(PrecedentRecord.model_validate(row))
        except ValidationError as exc:
            raise ValueError(f"invalid precedent record: {exc}") from exc
    ids = [record.id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate precedent IDs")

    ticker_counts = Counter(record.ticker for record in records)
    if require_minimum:
        if len(records) < 100:
            raise ValueError(f"expected at least 100 precedents; found {len(records)}")
        missing = sorted(ticker for ticker in SUPPORTED_TICKERS if ticker_counts[ticker] < 5)
        if missing:
            raise ValueError(f"tickers with fewer than five precedents: {', '.join(missing)}")

    for record in records:
        final_date = record.outcomes.series["stock"][-1].date
        if record.outcomes.series["stock"][0].date < record.event_date:
            raise ValueError(f"{record.id}: outcome anchor precedes event date")
        if final_date >= as_of:
            raise ValueError(f"{record.id}: 60-trading-day window is not complete before {as_of}")
    return records


def verify_source_urls(records: list[PrecedentRecord]) -> None:
    headers = {"User-Agent": get_settings().sec_user_agent}
    with httpx.Client(timeout=12, follow_redirects=True, headers=headers) as client:
        for record in records:
            time.sleep(0.2)
            response = client.get(str(record.source.url), headers={"Range": "bytes=0-0"})
            if response.status_code >= 400:
                raise ValueError(
                    f"{record.id}: source returned HTTP {response.status_code}: {record.source.url}"
                )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate EventLens historical precedent data.")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--check-urls", action="store_true", help="make HTTP requests to verify source URLs")
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    args = parser.parse_args()

    rows = json.loads(args.data.read_text(encoding="utf-8"))
    records = validate_dataset(rows, args.as_of)
    if args.check_urls:
        verify_source_urls(records)
    print(f"Validated {len(records)} precedents across {len({item.ticker for item in records})} tickers.")


if __name__ == "__main__":
    main()
