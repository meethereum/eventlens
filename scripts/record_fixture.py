#!/usr/bin/env python3
"""
record_fixture.py — capture a live /api/analyze run as a fixture JSON file.

Run this inside the backend container (or with the backend reachable):

    docker compose exec backend python /app/scripts/record_fixture.py \
        --query "Intel's CEO was just ousted. What should I expect?" \
        --ticker INTC \
        --as-of 2024-12-02 \
        --out /app/fixtures/intc_2024_12_02.json

Options:
    --query     Free-text query (required)
    --ticker    Ticker symbol (optional; engine will infer if omitted)
    --as-of     ISO date, e.g. 2024-12-02 (optional; defaults to today)
    --out       Output path (optional; defaults to fixtures/<ticker>_<as_of>.json)
    --host      Backend base URL (default http://localhost:8000)
    --no-demo   Force DEMO_MODE=0 so real cards are used (requires keys)

The script posts to /api/analyze, streams SSE events, records each event
with the actual inter-event delay (delay_ms), and writes the fixture file.

Timing note: delay_ms is capped at 5000 ms per event so fixtures don't
become unusably slow to replay if the live backend was under load.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    print("httpx is required: pip install httpx", file=sys.stderr)
    sys.exit(1)


MAX_DELAY_MS = 5_000
DEFAULT_HOST = "http://localhost:8000"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Record a live EventLens run as a fixture.")
    p.add_argument("--query", required=True, help="Free-text query")
    p.add_argument("--ticker", default="", help="Ticker symbol (optional)")
    p.add_argument("--as-of", dest="as_of", default="", help="ISO date (optional)")
    p.add_argument("--out", default="", help="Output path (optional)")
    p.add_argument("--host", default=DEFAULT_HOST, help=f"Backend URL (default {DEFAULT_HOST})")
    p.add_argument("--no-demo", action="store_true", help="Force live mode (DEMO_MODE=0)")
    return p.parse_args()


def default_output(ticker: str, as_of: str) -> Path:
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    stem = f"{ticker.lower()}_{as_of}" if ticker and as_of else f"fixture_{int(time.time())}"
    return fixtures_dir / f"{stem}.json"


def stream_events(host: str, query: str, ticker: str, as_of: str) -> list[dict[str, Any]]:
    """Stream /api/analyze and return recorded events with delay_ms."""
    url = f"{host}/api/analyze"
    payload = {"query": query, "ticker": ticker, "as_of": as_of}

    recorded: list[dict[str, Any]] = []
    last_ts = time.monotonic()

    print(f"→ POST {url}")
    print(f"  query  : {query}")
    print(f"  ticker : {ticker or '(infer)'}")
    print(f"  as_of  : {as_of or 'today'}")
    print()

    with httpx.Client(timeout=120) as client:
        with client.stream("POST", url, json=payload) as resp:
            resp.raise_for_status()
            buffer = ""
            for chunk in resp.iter_text():
                buffer += chunk
                frames = buffer.split("\n\n")
                buffer = frames.pop()

                for frame in frames:
                    data_line = next(
                        (l for l in frame.split("\n") if l.startswith("data:")), None
                    )
                    if not data_line:
                        continue
                    raw = data_line[len("data:"):].strip()
                    if not raw:
                        continue

                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    now = time.monotonic()
                    delay_ms = min(int((now - last_ts) * 1000), MAX_DELAY_MS)
                    last_ts = now

                    # Strip run_id and ts — these are injected at replay time
                    recorded.append({
                        "type": event.get("type"),
                        "delay_ms": delay_ms,
                        "data": event.get("data", {}),
                    })

                    etype = event.get("type", "?")
                    print(f"  [{delay_ms:4d}ms] {etype}")

                    if etype == "done":
                        return recorded

    return recorded


def main() -> None:
    args = parse_args()
    as_of = args.as_of or date.today().isoformat()
    ticker = args.ticker.upper()

    events = stream_events(args.host, args.query, ticker, as_of)

    if not events:
        print("\n✗ No events received — is the backend running?", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.out) if args.out else default_output(ticker, as_of)

    fixture = {
        "meta": {
            "query": args.query,
            "ticker": ticker,
            "as_of": as_of,
            "horizon_days": 20,
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fixture_version": "1",
        },
        "events": events,
    }

    out_path.write_text(json.dumps(fixture, indent=2))
    print(f"\n✓ Wrote {len(events)} events → {out_path}")


if __name__ == "__main__":
    main()
