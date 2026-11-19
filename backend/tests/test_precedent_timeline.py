from __future__ import annotations

import sys
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app


def test_precedent_timeline_endpoint_default():
    client = TestClient(app)
    response = client.get("/api/precedents/timeline")
    assert response.status_code == 200
    data = response.json()

    assert "query_prompt" in data
    assert "similar_company_events" in data
    assert len(data["similar_company_events"]) > 0

    first_company = data["similar_company_events"][0]
    assert "company_name" in first_company
    assert "timeline" in first_company
    assert len(first_company["timeline"]) > 0

    first_milestone = first_company["timeline"][0]
    assert "phase" in first_milestone
    assert "date" in first_milestone
    assert "stock_price" in first_milestone


def test_normal_queries_return_matching_event_precedents_not_cybersecurity():
    """Verify that normal queries do NOT return cybersecurity glitch, but instead event-specific news & precedents."""
    client = TestClient(app)

    # 1. Leadership / CEO ouster query
    res_ceo = client.get(
        "/api/precedents/timeline",
        params={"prompt": "Intel's CEO was just ousted. What should I expect?", "ticker": "INTC", "event_type": "CEO departure"},
    )
    assert res_ceo.status_code == 200
    data_ceo = res_ceo.json()
    assert "cybersecurity" not in data_ceo["incident_category"].lower()
    assert "leadership" in data_ceo["incident_category"].lower() or "governance" in data_ceo["incident_category"].lower()
    # First company should be Intel Corporation
    assert data_ceo["similar_company_events"][0]["stock_ticker"] == "INTC"
    assert data_ceo["similar_company_events"][0]["timeline"][0]["stock_price"] is not None

    # 2. Bank run & liquidity shock query
    res_bank = client.get(
        "/api/precedents/timeline",
        params={"prompt": "A regional bank experiences acute deposit flight and digital run", "ticker": "SCHW"},
    )
    assert res_bank.status_code == 200
    data_bank = res_bank.json()
    assert "cybersecurity" not in data_bank["incident_category"].lower()
    assert "bank" in data_bank["incident_category"].lower() or "liquidity" in data_bank["incident_category"].lower()
    assert any(c["stock_ticker"] in {"SCHW", "WAL", "KRE", "JPM"} for c in data_bank["similar_company_events"])

    # 3. Antitrust / Regulatory lawsuit query
    res_anti = client.get(
        "/api/precedents/timeline",
        params={"prompt": "Department of Justice files monopoly antitrust lawsuit", "ticker": "AAPL"},
    )
    assert res_anti.status_code == 200
    data_anti = res_anti.json()
    assert "cybersecurity" not in data_anti["incident_category"].lower()
    assert "antitrust" in data_anti["incident_category"].lower() or "regulatory" in data_anti["incident_category"].lower()
    assert data_anti["similar_company_events"][0]["stock_ticker"] == "AAPL"

    # 4. Operational defect / Safety grounding query
    res_safety = client.get(
        "/api/precedents/timeline",
        params={"prompt": "Airplane door plug blowout and emergency FAA fleet grounding", "ticker": "BA"},
    )
    assert res_safety.status_code == 200
    data_safety = res_safety.json()
    assert "cybersecurity" not in data_safety["incident_category"].lower()
    assert "operational" in data_safety["incident_category"].lower() or "safety" in data_safety["incident_category"].lower()
    assert data_safety["similar_company_events"][0]["stock_ticker"] == "BA"

    # 5. Earnings guidance collapse query
    res_earnings = client.get(
        "/api/precedents/timeline",
        params={"prompt": "Company reports severe Q2 revenue collapse, cuts guidance and slashes 15% workforce", "ticker": "INTC"},
    )
    assert res_earnings.status_code == 200
    data_earnings = res_earnings.json()
    assert "cybersecurity" not in data_earnings["incident_category"].lower()
    assert "earnings" in data_earnings["incident_category"].lower() or "guidance" in data_earnings["incident_category"].lower()

    # 6. Explicit cybersecurity query
    res_cyber = client.get(
        "/api/precedents/timeline",
        params={"prompt": "A major cybersecurity glitch takes down airlines and hospital IT", "ticker": "CRWD"},
    )
    assert res_cyber.status_code == 200
    data_cyber = res_cyber.json()
    assert "cybersecurity" in data_cyber["incident_category"].lower() or "it service disruption" in data_cyber["incident_category"].lower()
