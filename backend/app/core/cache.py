"""
Thin diskcache wrapper with per-source TTLs.

TTLs (seconds):
  FRED       6h   = 21600
  yfinance   1h   = 3600
  EDGAR      24h  = 86400
  GPR file   7d   = 604800
  NEWS       1h   = 3600
  EXPLANATION 24h = 86400
"""
from __future__ import annotations

import os
from functools import lru_cache

import diskcache

CACHE_DIR = os.environ.get("DISKCACHE_DIR", "/app/.cache")

# TTL constants (seconds)
TTL_FRED     = 21_600   # 6 h
TTL_YFINANCE =  3_600   # 1 h
TTL_EDGAR    = 86_400   # 24 h
TTL_GPR      = 604_800  # 7 d
TTL_NEWS     = 3_600    # 1 h
TTL_EXPLANATION = 86_400  # 24 h


@lru_cache(maxsize=1)
def get_cache() -> diskcache.Cache:
    return diskcache.Cache(CACHE_DIR, size_limit=512 * 1024 * 1024)  # 512 MB


def cache_get(key: str):
    return get_cache().get(key)


def cache_set(key: str, value, ttl: int) -> None:
    get_cache().set(key, value, expire=ttl)


def cache_key(*parts: str) -> str:
    return ":".join(parts)
