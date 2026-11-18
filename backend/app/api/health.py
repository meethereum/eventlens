"""
GET /api/health
Returns live/cached/demo status per data source, missing keys,
active model name and base-URL host, and LLM model availability.
"""
from __future__ import annotations

from urllib.parse import urlparse

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.models import DataSourceHealth, HealthResponse
from app.llm.client import check_model_availability

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    cfg = get_settings()

    host = urlparse(cfg.llm_base_url).hostname or cfg.llm_base_url

    # Check model availability (calls GET /models once, cached)
    model_available = check_model_availability()

    def _src(name: str, key_present: bool, note: str = "") -> DataSourceHealth:
        status = "demo" if cfg.is_demo_mode else ("live" if key_present else "demo")
        return DataSourceHealth(name=name, status=status, note=note)

    sources = [
        _src("FRED", bool(cfg.fred_api_key)),
        _src("yfinance", True, "no key required"),
        _src("SEC EDGAR", True, "no key required"),
        DataSourceHealth(
            name="GPR",
            status="demo" if cfg.is_demo_mode else "live",
            note="Caldara & Iacoviello (2022)",
        ),
        DataSourceHealth(
            name="LLM",
            status="demo" if not cfg.llm_api_key else "live",
            note=f"model: {cfg.llm_model}" + (
                " — not found in /models" if model_available is False else ""
            ),
        ),
    ]

    overall = "demo" if cfg.is_demo_mode else "ok"

    return HealthResponse(
        status=overall,
        demo_mode=cfg.is_demo_mode,
        missing_keys=cfg.missing_keys,
        llm_base_url_host=host,
        llm_model=cfg.llm_model,
        llm_model_available=model_available,
        data_sources=sources,
    )
