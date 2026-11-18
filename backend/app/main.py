"""
EventLens backend — FastAPI application entry point.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.analyze import router as analyze_router
from app.core.config import get_settings

cfg = get_settings()
logger = logging.getLogger("eventlens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "EventLens starting | demo=%s | llm_host=%s | model=%s",
        cfg.is_demo_mode,
        cfg.llm_base_url.split("//")[-1].split("/")[0],
        cfg.llm_model,
    )
    yield
    logger.info("EventLens shutting down")


app = FastAPI(
    title="EventLens API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS is only needed for local dev without nginx.
# In production, nginx proxies /api so there is no cross-origin request.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(analyze_router, prefix="/api")
