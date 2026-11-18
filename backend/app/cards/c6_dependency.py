"""
C6 — Cross-Sector Dependency

Loads curated edges from data/dependencies.json, computes the 20d
move of each proxy ETF, and calculates the stock's correlation with
the dominant linked sector. Produces graph data for react-flow
rendering in the inspector drawer.

Signal: weighted average of linked-sector moves × edge strength × sign.
Weight: fixed at 0.65 (curated judgment, moderate confidence).
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from app.core.models import CardOutput, Headline, Metric, Source
from app.core.yf_client import fetch_prices, fetch_returns
from app.scoring.math import (
    pct_change_over,
    series_to_output,
    signal_label,
    quality_score,
    TAU_DAILY,
)

CARD_ID    = "C6"
CARD_TITLE = "Cross-Sector Dependency"

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "dependencies.json"

# Proxy ETF map — what yfinance ticker to fetch for each node id
_NODE_TO_YF = {
    "SMH": "SMH", "TSM": "TSM", "CRWD": "CRWD", "SPR": "SPR",
    "WTI": None,   # commodity — skip, handled by C3
    "XLE": "XLE", "XLY": "XLY", "XLI": "XLI",
    "DGS10": None, # rate — skip, handled by C2
    "KRE": "KRE", "ITA": "ITA",
    "GPR": None,   # index — skip, handled by C7
    "XLY_2": "XLY",
}


def _load_edges() -> dict:
    with open(DATA_PATH) as f:
        return json.load(f)


def _edges_for_ticker(ticker: str, all_edges: list[dict]) -> list[dict]:
    """Return only edges that point TO this ticker."""
    return [e for e in all_edges if e["to"].upper() == ticker.upper()]


def fetch(ticker: str, as_of: str) -> CardOutput:
    t0 = time.time()
    warnings: list[str] = ["Dependency edges are curated judgment; citations TODO."]

    data = _load_edges()
    all_edges = data.get("edges", [])
    nodes = data.get("nodes", [])
    edges = _edges_for_ticker(ticker, all_edges)

    if not edges:
        warnings.append(f"No curated dependency edges for {ticker}")
        return CardOutput(
            id=CARD_ID, title=CARD_TITLE, status="done",
            as_of=as_of, fetched_at=datetime.utcnow().isoformat() + "Z",
            latency_ms=int((time.time() - t0) * 1000),
            headline=Headline(label="Linked sectors", value="N/A", unit=""),
            metrics=[], series=[],
            signal=0.0, label="neutral", weight=0.65, quality=0.3,
            reasoning=[f"No curated dependency edges exist for {ticker} in v1."],
            math=None,
            sources=[Source(name="data/dependencies.json (curated)", url="", retrieved_at=datetime.utcnow().isoformat() + "Z")],
            warnings=warnings,
        )

    # ── Fetch proxy ETF moves and correlation ──────────────────────────────
    stock_ret = fetch_returns(ticker, as_of=as_of)

    # Gather unique source node IDs that have a yfinance proxy
    source_nodes: list[str] = []
    for e in edges:
        src = e["from"]
        yf_ticker = _NODE_TO_YF.get(src)
        if yf_ticker and yf_ticker not in source_nodes:
            source_nodes.append(yf_ticker)

    # Fetch 20d moves for each proxy
    proxy_moves: dict[str, float] = {}
    proxy_prices: dict[str, pd.Series] = {}
    for yf_ticker in source_nodes:
        try:
            prices = fetch_prices(yf_ticker, as_of=as_of)
            move = pct_change_over(prices, 20)
            proxy_moves[yf_ticker] = move or 0.0
            proxy_prices[yf_ticker] = prices
        except Exception as exc:
            warnings.append(f"Could not fetch proxy {yf_ticker}: {exc}")
            proxy_moves[yf_ticker] = 0.0

    # ── Compute signal ────────────────────────────────────────────────────
    # s = sum(strength_i × move_i × sign_i) / sum(strength_i), clipped [-1, 1]
    num = 0.0
    denom = 0.0
    for e in edges:
        src = e["from"]
        yf_ticker = _NODE_TO_YF.get(src)
        if not yf_ticker or yf_ticker not in proxy_moves:
            continue
        move = proxy_moves[yf_ticker]
        strength = e["strength"]
        sign = e["sign"]
        num += strength * move * sign / 100.0  # normalize pct → fraction
        denom += strength

    s = float(np.clip(num / denom if denom > 0 else 0, -1.0, 1.0))
    w = 0.65

    # ── Correlation with dominant linked sector (highest-strength edge) ───
    dominant_edge = max(edges, key=lambda e: e["strength"])
    dominant_src = dominant_edge["from"]
    dominant_yf = _NODE_TO_YF.get(dominant_src)
    corr: float | None = None
    if dominant_yf and dominant_yf in proxy_prices:
        try:
            proxy_ret = fetch_returns(dominant_yf, as_of=as_of)
            combined = pd.concat([stock_ret.rename("stock"), proxy_ret.rename("proxy")], axis=1).dropna()
            if len(combined) >= 60:
                corr = float(combined["stock"].corr(combined["proxy"]))
        except Exception:
            pass

    # ── Quality ───────────────────────────────────────────────────────────
    fields_ok = len(proxy_moves) + (1 if corr is not None else 0)
    fields_total = len(source_nodes) + 1
    last_date = stock_ret.index[-1].date() if len(stock_ret) > 0 else datetime.utcnow().date()
    q = quality_score(last_date, fields_ok, max(fields_total, 1), TAU_DAILY)
    q = min(q, 0.88)  # cap — curated judgment limits quality

    # ── Build graph data for react-flow ───────────────────────────────────
    graph_nodes = []
    graph_edges = []
    seen_nodes: set[str] = set()

    for e in edges:
        src_id = e["from"]
        tgt_id = e["to"]
        if src_id not in seen_nodes:
            node_info = next((n for n in nodes if n["id"] == src_id), None)
            graph_nodes.append({
                "id": src_id,
                "label": node_info["label"] if node_info else src_id,
                "type": node_info["type"] if node_info else "unknown",
                "move20d": proxy_moves.get(_NODE_TO_YF.get(src_id, ""), None),
            })
            seen_nodes.add(src_id)
        if tgt_id not in seen_nodes:
            node_info = next((n for n in nodes if n["id"] == tgt_id), None)
            graph_nodes.append({
                "id": tgt_id,
                "label": node_info["label"] if node_info else tgt_id,
                "type": node_info["type"] if node_info else "ticker",
                "move20d": None,
            })
            seen_nodes.add(tgt_id)

        graph_edges.append({
            "source": src_id,
            "target": tgt_id,
            "channel": e["channel"],
            "sign": e["sign"],
            "strength": e["strength"],
            "rationale": e["rationale"],
        })

    # ── Metrics ───────────────────────────────────────────────────────────
    metrics = []
    for yf_ticker in source_nodes[:4]:  # top 4 proxies
        metrics.append(Metric(
            name=f"{yf_ticker} 20d",
            value=round(proxy_moves.get(yf_ticker, 0), 2),
            unit="%",
        ))
    if corr is not None:
        metrics.append(Metric(
            name=f"Corr {ticker}-{dominant_yf} (252d)",
            value=round(corr, 2),
            unit="",
        ))

    # ── Reasoning ─────────────────────────────────────────────────────────
    linked_desc = ", ".join(
        f"{_NODE_TO_YF.get(e['from'], e['from'])} {proxy_moves.get(_NODE_TO_YF.get(e['from'], ''), 0):+.1f}%"
        for e in edges[:3]
    )
    corr_str = f"{corr:.2f}" if corr is not None else "N/A"

    reasoning = [
        f"{len(edges)} curated dependency edges connect to {ticker}. "
        f"Top linked sectors (20d): {linked_desc}.",
        f"The strongest edge is {dominant_src} → {ticker} via {dominant_edge['channel']} "
        f"(strength {dominant_edge['strength']}, sign {'+' if dominant_edge['sign'] > 0 else '−'}). "
        f"{dominant_edge['rationale'][:120]}...",
        f"The 252-day correlation between {ticker} and {dominant_yf or dominant_src} is {corr_str}. "
        f"{'Moderate co-movement means sector weakness compounds company headwinds.' if corr is not None and abs(corr) > 0.4 else 'Low correlation suggests the dependency link is structural rather than reflected in daily price action.'}",
        f"Weighted signal s = {s:.2f} ({signal_label(s)}). "
        f"Curated edges are judgment — treat with caution.",
    ]

    latency_ms = int((time.time() - t0) * 1000)

    # ── Series for sparkline (dominant proxy) ──────────────────────────────
    spark_series = []
    if dominant_yf and dominant_yf in proxy_prices:
        spark_series = series_to_output(proxy_prices[dominant_yf].tail(250))

    return CardOutput(
        id=CARD_ID,
        title=CARD_TITLE,
        status="done",
        as_of=as_of,
        fetched_at=datetime.utcnow().isoformat() + "Z",
        latency_ms=latency_ms,
        headline=Headline(
            label="Linked sectors (20d avg)",
            value=round(float(np.mean(list(proxy_moves.values()))) if proxy_moves else 0, 2),
            unit="%",
        ),
        metrics=metrics,
        series=spark_series,
        signal=round(s, 4),
        label=signal_label(s),
        weight=round(w, 3),
        quality=round(q, 3),
        reasoning=reasoning,
        math={
            "formula": "s = sum(strength_i × move_i × sign_i) / sum(strength_i), clipped [-1,1]",
            "inputs": {
                "n_edges": len(edges),
                "dominant_edge": f"{dominant_src}→{ticker}",
                "dominant_strength": dominant_edge["strength"],
                "dominant_sign": dominant_edge["sign"],
                "corr": round(corr, 4) if corr is not None else None,
            },
            "contribution": None,
        },
        sources=[
            Source(name="data/dependencies.json (curated)", url="", retrieved_at=datetime.utcnow().isoformat() + "Z"),
            *[Source(name=f"yfinance {yf_t}", url=f"https://finance.yahoo.com/quote/{yf_t}",
                     retrieved_at=datetime.utcnow().isoformat() + "Z")
              for yf_t in source_nodes[:3]],
        ],
        warnings=warnings,
    )
