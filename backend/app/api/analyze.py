"""
POST /api/analyze   — streams SSE events for the full analysis pipeline
GET  /api/analyze/status/{run_id}  — quick status check
GET  /api/cards/{card_id}/inspect?run_id=...  — full card detail
"""
from __future__ import annotations

import time
import uuid
from datetime import date

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.demo_router import run_analysis
from app.core.run_store import get as get_run

router = APIRouter()


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    query: str
    ticker: str = ""          # optional pre-parsed ticker; engine will parse if empty
    as_of: str = ""           # ISO date; defaults to today


# ---------------------------------------------------------------------------
# POST /api/analyze
# ---------------------------------------------------------------------------

@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    run_id = str(uuid.uuid4())
    as_of = req.as_of or date.today().isoformat()
    ticker = req.ticker.upper() if req.ticker else _extract_ticker_hint(req.query)

    async def event_generator():
        try:
            async for chunk in run_analysis(
                query=req.query,
                ticker=ticker,
                as_of=as_of,
                run_id=run_id,
            ):
                # chunk is already a full "data: {...}\n\n" string.
                # Yield it as raw bytes so EventSourceResponse doesn't
                # double-wrap it.
                yield chunk
        except Exception as exc:
            from app.core.events import SSEEvent
            yield SSEEvent(
                type="error",
                run_id=run_id,
                ts=time.time(),
                data={"message": str(exc), "detail": ""},
            ).to_sse()

    # media_type text/event-stream, no extra wrapping
    from starlette.responses import StreamingResponse
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# GET /api/cards/{card_id}/inspect
# ---------------------------------------------------------------------------

@router.get("/cards/{card_id}/inspect")
async def inspect_card(card_id: str, run_id: str = Query(default="")):
    if not run_id:
        return JSONResponse(status_code=400, content={"detail": "run_id is required"})

    ctx = get_run(run_id)
    if ctx is None:
        return JSONResponse(status_code=404, content={"detail": f"run {run_id} not found"})

    card = ctx.cards.get(card_id.upper())
    if card is None:
        return JSONResponse(
            status_code=404,
            content={"detail": f"card {card_id} not found in run {run_id}"},
        )

    return card.model_dump()


# ---------------------------------------------------------------------------
# GET /api/analyze/status/{run_id}
# ---------------------------------------------------------------------------

@router.get("/analyze/status/{run_id}")
async def run_status(run_id: str):
    ctx = get_run(run_id)
    if ctx is None:
        return JSONResponse(status_code=404, content={"detail": "run not found"})
    return {
        "run_id": ctx.run_id,
        "ticker": ctx.ticker,
        "as_of": ctx.as_of,
        "cards_done": list(ctx.cards.keys()),
        "has_aggregate": ctx.aggregate is not None,
        "has_verdict": ctx.verdict is not None,
        "elapsed_ms": ctx.elapsed_ms(),
    }


# ---------------------------------------------------------------------------
# POST /api/baseline — plain LLM comparison (no card context)
# ---------------------------------------------------------------------------

class BaselineRequest(BaseModel):
    query: str


@router.post("/baseline")
async def baseline(req: BaselineRequest):
    """Plain LLM response with no card context — for the stretch comparison toggle."""
    from app.llm.baseline import get_baseline_response
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_baseline_response, req.query)
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Simple keyword→ticker map for the scripted demos when ticker is not sent
_TICKER_HINTS: list[tuple[list[str], str]] = [
    (["intel", "intc"],           "INTC"),
    (["nvidia", "nvda"],          "NVDA"),
    (["exxon", "xom"],            "XOM"),
    (["jpmorgan", "jpm", "jp morgan"], "JPM"),
    (["apple", "aapl"],           "AAPL"),
    (["microsoft", "msft"],       "MSFT"),
    (["amazon", "amzn"],          "AMZN"),
    (["starbucks", "sbux"],       "SBUX"),
    (["disney", "dis"],           "DIS"),
    (["boeing", "ba"],            "BA"),
    (["raytheon", "rtx"],         "RTX"),
    (["chevron", "cvx"],          "CVX"),
    (["schwab", "schw"],          "SCHW"),
    (["unitedhealth", "unh"],     "UNH"),
    (["gm", "general motors"],    "GM"),
]

def _extract_ticker_hint(query: str) -> str:
    q = query.lower()
    for keywords, ticker in _TICKER_HINTS:
        if any(kw in q for kw in keywords):
            return ticker
    return "UNKNOWN"
