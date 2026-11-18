"""
Geopolitical Risk Index (GPR) data source.

The GPR index is published by Caldara & Iacoviello (2022, American Economic Review)
at https://www.matteoiacoviello.com/gpr.htm.

Strategy:
1. On first call, try to refresh from the website (scrape links, download Excel).
2. If refresh fails, fall back to bundled copy in data/gpr/.
3. Cache with 7-day TTL.

The site publishes monthly and daily files with date-stamped names
(e.g. data_gpr_daily_recent_YYYYMMDD.xls), so we scrape the page to find
current links rather than hardcoding URLs.

Attribution: "Data downloaded from https://www.matteoiacoviello.com/gpr.htm
on <date>", citing Caldara and Iacoviello (2022), American Economic Review.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime
from pathlib import Path

import httpx
import pandas as pd

from app.core.cache import cache_get, cache_key, cache_set, TTL_GPR

logger = logging.getLogger("eventlens.gpr")

GPR_PAGE_URL = "https://www.matteoiacoviello.com/gpr.htm"
BUNDLED_DIR = Path(__file__).parent.parent.parent / "data" / "gpr"
CACHE_KEY = "gpr_daily_series"


def _find_excel_links(html: str) -> dict[str, str | None]:
    """
    Scrape the GPR page for links to daily and monthly Excel files.
    Returns {"daily": url, "monthly": url}.
    """
    links: dict[str, str | None] = {"daily": None, "monthly": None}

    # Look for hrefs containing "gpr" and "daily" or "monthly" with .xls extension
    href_pattern = r'href=["\']([^"\']*(?:gpr|GPR)[^"\']*(?:\.xls|\.xlsx))["\']'
    matches = re.findall(href_pattern, html, re.IGNORECASE)

    for url in matches:
        lower = url.lower()
        if "daily" in lower:
            links["daily"] = url if url.startswith("http") else f"https://www.matteoiacoviello.com/{url.lstrip('/')}"
        elif "monthly" in lower:
            links["monthly"] = url if url.startswith("http") else f"https://www.matteoiacoviello.com/{url.lstrip('/')}"

    return links


def _load_bundled() -> pd.Series:
    """Load the bundled GPR daily file as a pandas Series."""
    bundled_files = sorted(BUNDLED_DIR.glob("data_gpr_daily*.xls*"), reverse=True)
    if not bundled_files:
        raise FileNotFoundError("No bundled GPR file found")

    logger.info("Loading bundled GPR: %s", bundled_files[0])
    df = pd.read_excel(bundled_files[0], engine="xlrd" if bundled_files[0].suffix == ".xls" else None)

    # The file has columns: date, GPRC, GPRD, ... — we want GPRD (daily GPR)
    # Normalize column names
    df.columns = [c.strip().upper() for c in df.columns]

    date_col = df.columns[0]  # first column is the date
    gpr_col = "GPRD" if "GPRD" in df.columns else ("GPRC" if "GPRC" in df.columns else df.columns[1])

    s = pd.Series(df[gpr_col].values, index=pd.to_datetime(df[date_col]), dtype=float)
    s = s.sort_index().dropna()
    s.name = "GPR"
    return s


def _refresh_from_web() -> pd.Series:
    """
    Fetch the GPR page, find the current daily Excel link, download, and parse.
    Raises on any failure.
    """
    logger.info("Refreshing GPR from %s", GPR_PAGE_URL)

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        resp = client.get(GPR_PAGE_URL)
        resp.raise_for_status()
        html = resp.text

    links = _find_excel_links(html)
    daily_url = links.get("daily")
    if not daily_url:
        raise ValueError("Could not find daily GPR Excel link on the page")

    logger.info("Found GPR daily link: %s", daily_url)

    with httpx.Client(timeout=60, follow_redirects=True) as client:
        resp = client.get(daily_url)
        resp.raise_for_status()

    # Parse the downloaded Excel
    import io
    df = pd.read_excel(io.BytesIO(resp.content))

    df.columns = [c.strip().upper() for c in df.columns]
    date_col = df.columns[0]
    gpr_col = "GPRD" if "GPRD" in df.columns else ("GPRC" if "GPRC" in df.columns else df.columns[1])

    s = pd.Series(df[gpr_col].values, index=pd.to_datetime(df[date_col]), dtype=float)
    s = s.sort_index().dropna()
    s.name = "GPR"
    return s


def fetch_gpr(as_of: str | None = None) -> pd.Series:
    """
    Return the GPR daily index as a pandas Series (DatetimeIndex → float).
    Clips to as_of date.

    Tries web refresh first (7-day cache), falls back to bundled copy.
    """
    cached = cache_get(CACHE_KEY)
    if cached is not None:
        s = cached
    else:
        try:
            s = _refresh_from_web()
            cache_set(CACHE_KEY, s, TTL_GPR)
            logger.info("GPR refreshed from web, %d points", len(s))
        except Exception as exc:
            logger.warning("GPR web refresh failed (%s), using bundled copy", exc)
            s = _load_bundled()
            cache_set(CACHE_KEY, s, TTL_GPR)  # still cache to avoid re-reading file

    # Clip to as_of
    if as_of:
        s = s[s.index <= pd.Timestamp(as_of)]

    return s


def get_gpr_metadata() -> dict:
    """Return metadata about the GPR data source for health/sourcing."""
    cached = cache_get(CACHE_KEY)
    source = "web" if cached is not None else "bundled"
    last_date = str(cached.index[-1].date()) if cached is not None and len(cached) > 0 else "unknown"

    bundled_files = sorted(BUNDLED_DIR.glob("data_gpr_daily*.xls*"), reverse=True)
    bundled_date = None
    if bundled_files:
        # Try to extract date from filename
        match = re.search(r"(\d{8})", bundled_files[0].name)
        if match:
            bundled_date = f"file dated {match.group(1)}"

    return {
        "source": source,
        "last_date": last_date,
        "bundled_file": str(bundled_files[0].name) if bundled_files else "none",
        "bundled_note": bundled_date or "date unknown",
        "attribution": "Caldara and Iacoviello (2022), American Economic Review",
        "url": GPR_PAGE_URL,
    }
