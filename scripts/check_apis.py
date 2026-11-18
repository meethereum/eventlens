#!/usr/bin/env python3
"""
check_apis.py — verify every data series used by EventLens actually exists.

Run inside the backend container (or with the venv active):

    docker compose exec backend python /app/scripts/check_apis.py

Requires FRED_API_KEY to be set.  yfinance checks need no key.
Exits with code 1 if any series fails so it can be used in CI.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# ── Add backend to path ───────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
# Also add /app (the container's WORKDIR) so imports work inside Docker
sys.path.insert(0, "/app")

# ── Load .env if running outside Docker ───────────────────────────────────
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

import httpx
import pandas as pd
import yfinance as yf

# ── Series to check ───────────────────────────────────────────────────────

FRED_SERIES = [
    # C1
    ("DTWEXBGS",   "USD DXY broad"),
    # C2
    ("DGS10",      "10y Treasury"),
    ("DFF",        "Fed Funds Rate"),
    ("T10Y2Y",     "10y-2y spread"),
    ("CPIAUCSL",   "CPI all urban"),
    # C3
    ("DCOILWTICO", "WTI crude"),
    ("DCOILBRENTEU", "Brent crude"),
    # C4
    ("VIXCLS",     "VIX"),
    # C7
    ("USEPUINDXD", "US Economic Policy Uncertainty"),
]

YFINANCE_TICKERS = [
    # Stocks
    "NVDA", "INTC", "AAPL", "MSFT", "GM", "SBUX", "AMZN",
    "DIS", "BA", "RTX", "XOM", "CVX", "JPM", "SCHW", "UNH",
    # Benchmarks
    "SPY",
    # Sector ETFs
    "XLK", "XLY", "XLC", "XLI", "XLE", "XLF", "XLV",
    # C6 proxy ETFs / tickers
    "SMH", "KRE", "ITA",
    # C6 individual supplier/customer tickers
    "TSM", "CRWD", "SPR",
]
YFINANCE_TICKERS = list(dict.fromkeys(YFINANCE_TICKERS))  # deduplicate

# ── EDGAR tickers to verify CIK lookup ────────────────────────────────────
EDGAR_TICKERS = [
    "NVDA", "INTC", "AAPL", "MSFT", "GM", "SBUX", "AMZN",
    "DIS", "BA", "RTX", "XOM", "CVX", "JPM", "SCHW", "UNH",
]

# ─────────────────────────────────────────────────────────────────────────

FRED_BASE = "https://api.stlouisfed.org/fred"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

results: list[tuple[str, str, bool, str]] = []  # (source, id, ok, note)


def check_fred(series_id: str, label: str, api_key: str) -> None:
    try:
        url = f"{FRED_BASE}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "limit": 1,
            "sort_order": "desc",
        }
        resp = httpx.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            obs = resp.json().get("observations", [])
            note = f"latest={obs[0]['date']} value={obs[0]['value']}" if obs else "no observations"
            ok = bool(obs)
        else:
            note = f"HTTP {resp.status_code}"
            ok = False
    except Exception as e:
        note = str(e)
        ok = False
    results.append(("FRED", f"{series_id} ({label})", ok, note))
    time.sleep(0.3)  # polite rate limit


def check_edgar_cik(ticker: str, user_agent: str) -> None:
    """Verify SEC EDGAR can resolve ticker → CIK and fetch companyfacts."""
    try:
        headers = {"User-Agent": user_agent}
        # Step 1: CIK lookup
        with httpx.Client(timeout=15, headers=headers) as c:
            resp = c.get("https://www.sec.gov/files/company_tickers.json")
            resp.raise_for_status()
            cik_map = resp.json()

        cik = None
        for entry in cik_map.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                cik = str(entry["cik_str"]).zfill(10)
                break

        if not cik:
            results.append(("EDGAR", f"{ticker} (CIK lookup)", False, "ticker not found"))
            return

        # Step 2: Verify companyfacts endpoint returns 200
        facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json"
        headers2 = {**headers, "Host": "data.sec.gov"}
        with httpx.Client(timeout=30, headers=headers2) as c:
            resp2 = c.get(facts_url)
        if resp2.status_code == 200:
            facts = resp2.json()
            n_concepts = len(facts.get("facts", {}).get("us-gaap", {}))
            results.append(("EDGAR", f"{ticker} (CIK {cik})", True, f"companyfacts OK, {n_concepts} us-gaap concepts"))
        else:
            results.append(("EDGAR", f"{ticker} (CIK {cik})", False, f"companyfacts HTTP {resp2.status_code}"))
    except Exception as e:
        results.append(("EDGAR", ticker, False, str(e)[:80]))


def check_yfinance(ticker: str) -> None:
    """Use the same retry logic as the production yf_client."""
    import time as _time

    last_exc = None
    for attempt in range(3):
        try:
            df = yf.download(ticker, period="5d", auto_adjust=True, progress=False)
            if df is not None and not df.empty:
                # Flatten MultiIndex if present
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                last = df.index[-1].strftime("%Y-%m-%d")
                if "Close" in df.columns:
                    close = float(df["Close"].iloc[-1])
                else:
                    close = float(df.iloc[-1, 0])
                results.append(("yfinance", ticker, True, f"latest={last} close={close:.2f}"))
                return
        except Exception as e:
            last_exc = e

        if attempt < 2:
            _time.sleep(2.0 * (attempt + 1))

    if last_exc:
        results.append(("yfinance", ticker, False, str(last_exc)[:80]))
    else:
        results.append(("yfinance", ticker, False, "empty response after 3 retries"))


def main() -> int:
    api_key = os.environ.get("FRED_API_KEY", "")

    print(f"\n{BOLD}EventLens API Series Checker{RESET}")
    print("=" * 60)

    if not api_key:
        print(f"{YELLOW}⚠  FRED_API_KEY not set — skipping FRED checks{RESET}\n")
    else:
        print(f"\n{BOLD}FRED series ({len(FRED_SERIES)} checks){RESET}")
        for sid, label in FRED_SERIES:
            check_fred(sid, label, api_key)
            status = f"{GREEN}✓{RESET}" if results[-1][2] else f"{RED}✗{RESET}"
            print(f"  {status}  {sid:20s}  {label:35s}  {results[-1][3]}")

    print(f"\n{BOLD}yfinance tickers ({len(YFINANCE_TICKERS)} checks){RESET}")
    for i, tkr in enumerate(YFINANCE_TICKERS):
        check_yfinance(tkr)
        status = f"{GREEN}✓{RESET}" if results[-1][2] else f"{RED}✗{RESET}"
        print(f"  {status}  {tkr:10s}  {results[-1][3]}")
        # Polite delay between yfinance requests (Yahoo rate-limits aggressively)
        if i < len(YFINANCE_TICKERS) - 1:
            time.sleep(0.5)

    # ── EDGAR CIK verification ────────────────────────────────────────────
    print(f"\n{BOLD}SEC EDGAR CIK lookup ({len(EDGAR_TICKERS)} checks){RESET}")
    sec_ua = os.environ.get("SEC_USER_AGENT", "")
    if not sec_ua or "your@email.com" in sec_ua:
        print(f"  {YELLOW}⚠  SEC_USER_AGENT not set (using placeholder) — skipping EDGAR checks{RESET}")
    else:
        for tkr in EDGAR_TICKERS:
            check_edgar_cik(tkr, sec_ua)
            status = f"{GREEN}✓{RESET}" if results[-1][2] else f"{RED}✗{RESET}"
            print(f"  {status}  {tkr:10s}  {results[-1][3]}")
            time.sleep(0.2)  # stay under 5 req/s

    # ── Summary ───────────────────────────────────────────────────────────
    total  = len(results)
    passed = sum(1 for r in results if r[2])
    failed = total - passed

    print(f"\n{'='*60}")
    print(f"{BOLD}Results: {passed}/{total} passed{RESET}", end="")
    if failed:
        print(f"  {RED}({failed} failed){RESET}")
        print(f"\n{RED}Failed:{RESET}")
        for source, sid, ok, note in results:
            if not ok:
                print(f"  {source:10s}  {sid:30s}  {note}")
    else:
        print(f"  {GREEN}(all OK){RESET}")

    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
