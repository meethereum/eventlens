"""
SEC EDGAR XBRL client.

Fetches companyfacts JSON from data.sec.gov.
- Ticker → CIK via company_tickers.json
- Caches CIK map permanently, companyfacts for 24h
- Sends SEC_USER_AGENT on every request (required by fair-use policy)
- Stays under 5 req/s (httpx client with 0.2s delay between calls)
- Respects filed <= as_of: only uses facts with end date <= as_of
"""
from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any

import httpx
import pandas as pd

from app.core.cache import cache_get, cache_key, cache_set, TTL_EDGAR
from app.core.config import get_settings

logger = logging.getLogger("eventlens.edgar")

CIK_MAP_URL  = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL    = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

# The SEC ticker map retains historical/duplicate ticker assignments.  EventLens
# has a fixed v1 universe, so use the current issuer CIK for those symbols rather
# than accepting the first duplicate entry returned by the map.
CIK_OVERRIDES = {
    "NVDA": "0001045810", "INTC": "0000050863", "AAPL": "0000320193",
    "MSFT": "0000789019", "GM": "0001467858", "SBUX": "0000829224",
    "AMZN": "0001018724", "DIS": "0001744489", "BA": "0000012927",
    "RTX": "0000101829", "XOM": "0000034088", "CVX": "0000093410",
    "JPM": "0000019617", "SCHW": "0000316709", "UNH": "0000731766",
}

# XBRL concept names used by C8-C10
CONCEPTS = {
    # Balance sheet
    "assets_current":       "us-gaap:AssetsCurrent",
    "liabilities_current":  "us-gaap:LiabilitiesCurrent",
    "assets":               "us-gaap:Assets",
    "stockholders_equity":   "us-gaap:StockholdersEquity",
    "long_term_debt":       "us-gaap:LongTermDebt",
    "total_debt":            "us-gaap:Debt",
    "cash":                 "us-gaap:CashAndCashEquivalents",
    "cash_short_term_inv":  "us-gaap:CashAndCashEquivalentsAtCarryingValue",
    # Income statement
    "revenue":              "us-gaap:Revenues",
    "revenue_alt":          "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    "net_income":           "us-gaap:NetIncomeLoss",
    "interest_expense":     "us-gaap:InterestExpense",
    "operating_income":     "us-gaap:OperatingIncomeLoss",
    "diluted_eps":          "us-gaap:EarningsPerShareDiluted",
    "diluted_eps_alt":      "us-gaap:IncomeLossFromContinuingOperationsPerDilutedShare",
    "shares_diluted":       "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding",
    "gross_profit":         "us-gaap:GrossProfit",
}


def _headers() -> dict:
    return {
        "User-Agent": get_settings().sec_user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov",
    }


def _headers_data() -> dict:
    h = _headers()
    h["Host"] = "data.sec.gov"
    return h


# ---------------------------------------------------------------------------
# CIK lookup
# ---------------------------------------------------------------------------

_CIK_CACHE: dict[str, str] = {}  # ticker → CIK string (zero-padded 10)


def get_cik(ticker: str) -> str | None:
    """Return the 10-digit zero-padded CIK for the given ticker."""
    ticker = ticker.upper()
    if ticker in CIK_OVERRIDES:
        return CIK_OVERRIDES[ticker]
    if ticker in _CIK_CACHE:
        return _CIK_CACHE[ticker]

    ck = cache_key("edgar", "cik_map")
    cik_map = cache_get(ck)

    if cik_map is None:
        logger.info("EDGAR: fetching CIK map")
        with httpx.Client(timeout=30, headers=_headers()) as c:
            resp = c.get(CIK_MAP_URL)
            resp.raise_for_status()
            cik_map = resp.json()
        cache_set(ck, cik_map, TTL_EDGAR)

    # cik_map is { "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ... }
    for entry in cik_map.values():
        if entry.get("ticker", "").upper() == ticker:
            cik = str(entry["cik_str"]).zfill(10)
            _CIK_CACHE[ticker] = cik
            return cik

    return None


# ---------------------------------------------------------------------------
# Companyfacts fetch
# ---------------------------------------------------------------------------

def get_companyfacts(ticker: str, as_of: str | None = None) -> dict[str, Any]:
    """
    Fetch the full companyfacts JSON for a ticker.
    Returns the raw dict; caller is responsible for extracting concepts.
    """
    cik = get_cik(ticker)
    if not cik:
        raise ValueError(f"Could not find CIK for ticker {ticker}")

    ck = cache_key("edgar", "facts", cik)
    facts = cache_get(ck)

    if facts is None:
        logger.info("EDGAR: fetching companyfacts for %s (CIK %s)", ticker, cik)
        url = FACTS_URL.format(cik=int(cik))
        with httpx.Client(timeout=60, headers=_headers_data()) as c:
            resp = c.get(url)
            if resp.status_code == 404:
                raise ValueError(f"EDGAR: no companyfacts for CIK {cik}")
            resp.raise_for_status()
            facts = resp.json()
        cache_set(ck, facts, TTL_EDGAR)
        time.sleep(0.2)  # stay under 5 req/s

    return facts


def get_filings_near_date(ticker: str, event_date: str, window_days: int = 1) -> list[dict[str, str]]:
    """Return company 8-K/10-K/10-Q filings near a date with official filing URLs."""
    cik = get_cik(ticker)
    if not cik:
        return []

    cache_id = cache_key("edgar", "submissions", cik)
    submissions = cache_get(cache_id)
    if submissions is None:
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        with httpx.Client(timeout=30, headers=_headers_data()) as client:
            response = client.get(url)
            response.raise_for_status()
            submissions = response.json()
        cache_set(cache_id, submissions, TTL_EDGAR)

    target = pd.Timestamp(event_date)
    forms = submissions.get("filings", {}).get("recent", {})
    dates = forms.get("filingDate", [])
    accepted_forms = forms.get("form", [])
    accession_numbers = forms.get("accessionNumber", [])
    primary_documents = forms.get("primaryDocument", [])
    results: list[dict[str, str]] = []

    for index, filed in enumerate(dates):
        filed_date = pd.Timestamp(filed)
        if abs((filed_date - target).days) > window_days:
            continue
        form = accepted_forms[index]
        if form not in {"8-K", "10-K", "10-Q"}:
            continue
        accession = accession_numbers[index]
        accession_path = accession.replace("-", "")
        document = primary_documents[index]
        results.append({
            "title": f"{form} filed {filed_date.date().isoformat()}",
            "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_path}/{document}",
            "date": filed_date.date().isoformat(),
            "source": "SEC EDGAR",
            "form": form,
        })
    return results[:5]


# ---------------------------------------------------------------------------
# XBRL extraction helpers
# ---------------------------------------------------------------------------

def _get_concept_facts(
    facts: dict,
    concept_key: str,
    as_of: str | None = None,
) -> pd.DataFrame:
    """
    Extract a concept from companyfacts JSON.
    Returns DataFrame with columns: [end, value, form, filed, fy, fp, frame].

    Filters to filed <= as_of and end <= as_of.
    """
    # concept_key is like "us-gaap:AssetsCurrent"
    taxonomy, concept = concept_key.split(":", 1)

    entities = facts.get("facts", {})
    tax_data = entities.get("dei", {}) if taxonomy == "dei" else entities.get("us-gaap", {})
    if taxonomy not in entities:
        # fallback: try both
        for tax in ("us-gaap", "dei", "ifrs-full"):
            if concept in entities.get(tax, {}):
                tax_data = entities[tax]
                break

    concept_data = tax_data.get(concept, {})
    units_data = concept_data.get("units", {})

    # Most financial concepts use "USD", some use "USD/shares"
    rows: list[dict] = []
    for unit, items in units_data.items():
        if unit in ("USD", "USD/shares", "shares"):
            for item in items:
                rows.append(item)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Convert dates
    if "end" in df.columns:
        df["end"] = pd.to_datetime(df["end"], errors="coerce")
    if "filed" in df.columns:
        df["filed"] = pd.to_datetime(df["filed"], errors="coerce")

    # Filter to as_of
    if as_of:
        as_of_ts = pd.Timestamp(as_of)
        if "filed" in df.columns:
            df = df[df["filed"] <= as_of_ts]
        if "end" in df.columns:
            df = df[df["end"] <= as_of_ts]

    return df.sort_values("end") if "end" in df.columns else df


def get_annual_value(
    facts: dict,
    concept_key: str,
    as_of: str | None = None,
    n_years_back: int = 5,
) -> pd.DataFrame:
    """
    Return annual (10-K) values for a concept.
    Filters to form == '10-K' and deduplicates by fiscal year.
    """
    df = _get_concept_facts(facts, concept_key, as_of)
    if df.empty:
        return df

    # Prefer 10-K filings
    if "form" in df.columns:
        annual = df[df["form"] == "10-K"].copy()
        if annual.empty:
            annual = df.copy()
    else:
        annual = df.copy()

    # Deduplicate by fiscal year (keep latest filed)
    if "fy" in annual.columns and "filed" in annual.columns:
        annual = annual.sort_values("filed").drop_duplicates(subset=["fy"], keep="last")

    # Limit to n_years_back
    if "end" in annual.columns and len(annual) > n_years_back:
        annual = annual.tail(n_years_back)

    return annual


def get_quarterly_value(
    facts: dict,
    concept_key: str,
    as_of: str | None = None,
    n_quarters_back: int = 8,
) -> pd.DataFrame:
    """
    Return quarterly (10-Q) values for a concept, plus latest 10-K as fallback.
    """
    df = _get_concept_facts(facts, concept_key, as_of)
    if df.empty:
        return df

    # Prefer 10-Q filings, but include 10-K for completeness
    if "form" in df.columns:
        quarterly = df[df["form"].isin(["10-Q", "10-K"])].copy()
    else:
        quarterly = df.copy()

    if "end" in quarterly.columns and len(quarterly) > n_quarters_back:
        quarterly = quarterly.tail(n_quarters_back)

    return quarterly


def get_ttm_value(
    facts: dict,
    concept_key: str,
    as_of: str | None = None,
) -> float | None:
    """
    Compute trailing twelve months value for a flow concept (revenue, net income, etc.)
    by summing the last 4 quarters of 10-Q data, or falling back to the latest 10-K annual value.
    """
    # Try quarterly first
    quarterly = get_quarterly_value(facts, concept_key, as_of, n_quarters_back=4)
    if not quarterly.empty and "val" in quarterly.columns and len(quarterly) >= 4:
        ttm = float(quarterly["val"].tail(4).sum())
        return ttm

    # Fall back to annual
    annual = get_annual_value(facts, concept_key, as_of, n_years_back=1)
    if not annual.empty and "val" in annual.columns:
        return float(annual["val"].iloc[-1])

    return None


def get_latest_value(
    facts: dict,
    concept_key: str,
    as_of: str | None = None,
) -> float | None:
    """Get the most recent value for a concept (point-in-time, not flow)."""
    df = _get_concept_facts(facts, concept_key, as_of)
    if df.empty or "val" not in df.columns:
        return None
    return float(df["val"].iloc[-1])
