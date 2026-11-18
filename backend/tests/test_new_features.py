from __future__ import annotations

import asyncio
import json

from app.core.models import CardOutput, MathDetail, Series
from app.core.models import Source
from app.core.models import AggregateResult
from app.precedents.engine import find_precedents
from app.scoring.simulation import ScenarioOverrides, simulate


def _card(card_id: str, signal: float, direction: int = 1) -> CardOutput:
    return CardOutput(
        id=card_id,
        title=card_id,
        status="done",
        signal=signal,
        weight=0.7,
        quality=1.0,
        math=MathDetail(formula="", inputs={"d": direction}),
    )


def test_scenario_override_changes_only_matching_factor_card():
    cards = [_card("C1", 0.1), _card("C2", -0.2)]

    baseline = simulate(cards, ScenarioOverrides())
    changed = simulate(cards, ScenarioOverrides(usd_pct=20))

    assert changed["factor_impacts"] == [
        {"card_id": "C1", "factor": "usd_pct", "signal_change": 0.25}
    ]
    assert changed["card_contributions"]["C2"] == baseline["card_contributions"]["C2"]
    assert changed["composite_signal"] > baseline["composite_signal"]


def test_verified_precedents_are_served_as_historical_data():
    matches = find_precedents("NVDA", "AI competitive shock", "2025-01-27")
    assert len(matches) == 5
    assert all(match["source"]["url"].startswith("https://www.sec.gov/") for match in matches)
    assert all(match["event_date"] < "2025-01-27" for match in matches)


def test_precedent_match_returns_completed_outcomes_only():
    matches = find_precedents("NVDA", "AI competitive shock", "2025-01-28")
    assert len(matches) == 5
    assert all(match["days_before_as_of"] > 60 for match in matches)


def test_simulation_adjustment_is_clamped_at_signal_bounds():
    card = _card("C1", 0.95)
    result = simulate([card], ScenarioOverrides(usd_pct=20))
    assert result["card_contributions"]["C1"] == 1.0


def test_simulation_presentation_ranks_human_named_drivers():
    from app.scoring.simulation import build_presentation

    cards = [_card("C1", 0.1), _card("C3", -0.2)]
    baseline = simulate(cards, ScenarioOverrides())
    scenario = simulate(cards, ScenarioOverrides(usd_pct=20, oil_pct=20))
    presentation = build_presentation(scenario, {"composite_signal": baseline["composite_signal"]})

    assert presentation["headline"] in {
        "The evidence leans supportive",
        "The evidence points to headwinds",
        "The evidence is mixed",
    }
    assert [driver["name"] for driver in presentation["drivers"]] == ["Oil prices", "US dollar"]
    assert presentation["drivers"][0]["weight"] == 100
    assert all("card_id" not in driver for driver in presentation["drivers"])
    assert presentation["change_summary"] == "This change makes the outlook somewhat more supportive than the baseline."


def test_unusual_day_detection_returns_large_series_outlier():
    from app.api.analyze import _unusual_days

    card = _card("C5", 0.1)
    card.series = [
        Series(t=f"2025-01-{day:02d}", v=float(200 if day == 15 else 100))
        for day in range(1, 16)
    ]

    days = _unusual_days(card)
    assert len(days) == 1
    assert days[0]["date"] == "2025-01-15"
    assert days[0]["daily_percentage_move"] > 3.5
    assert days[0]["adjusted_price"] == 200
    assert days[0]["robust_score"] >= 3.5


def test_invalid_llm_citations_fall_back_to_template(monkeypatch):
    from types import SimpleNamespace

    import app.llm.synthesis as synthesis

    card = _card("C1", -0.2)
    aggregate = AggregateResult(
        composite_signal=-0.2,
        evidence_strength=0.1,
        coverage=1,
        scenarios=[],
        card_contributions={"C1": -0.2},
    )
    llm_output = synthesis.SynthesisOutput(
        headline="Test",
        summary="Unsupported citation [C99].",
        key_drivers=[],
        counter_evidence=[],
        scenarios=[],
        confidence_statement="",
    )
    monkeypatch.setattr(synthesis, "get_settings", lambda: SimpleNamespace(
        llm_api_key="configured",
        llm_model="test-model",
        llm_fallback_model="",
    ))
    monkeypatch.setattr(
        synthesis,
        "json_completion",
        lambda **kwargs: (llm_output, "{}", False),
    )

    verdict, verified = synthesis.synthesize_verdict(
        "test query",
        {"ticker": "INTC", "as_of": "2024-12-02"},
        {"C1": card},
        aggregate,
    )

    assert not verified
    assert verdict.is_fallback
    assert "[C99]" not in verdict.summary


def test_new_api_routes_work_with_a_completed_run(monkeypatch):
    from fastapi.testclient import TestClient

    from app.core.events import RunContext
    from app.core.run_store import put
    from app.main import app

    card = _card("C5", 0.1)
    card.series = [
        Series(t=f"2025-01-{day:02d}", v=float(200 if day == 15 else 100))
        for day in range(1, 16)
    ]
    card.related_series = {
        "sector": [Series(t=point.t, v=100 + index * 0.1) for index, point in enumerate(card.series)],
        "market": [Series(t=point.t, v=100 + index * 0.05) for index, point in enumerate(card.series)],
    }
    card.sources = [
        Source(name="Stock prices", url="https://finance.yahoo.com/quote/INTC", retrieved_at="2025-01-20"),
        Source(name="Sector prices", url="https://finance.yahoo.com/quote/XLK", retrieved_at="2025-01-20"),
        Source(name="Market prices", url="https://finance.yahoo.com/quote/SPY", retrieved_at="2025-01-20"),
    ]
    ctx = RunContext(run_id="feature-api-test", ticker="INTC", as_of="2025-01-20")
    ctx.cards[card.id] = card
    ctx.cards["C1"] = _card("C1", 0.1)
    ctx.aggregate = AggregateResult(
        composite_signal=0.1,
        evidence_strength=0.1,
        coverage=1,
        scenarios=[],
        card_contributions={"C1": 0.1},
    )
    put(ctx)
    llm_calls = []
    monkeypatch.setattr(
        "app.core.config.get_settings",
        lambda: type("Settings", (), {"llm_api_key": ""})(),
    )
    monkeypatch.setattr(
        "app.llm.client.chat_completion",
        lambda **kwargs: llm_calls.append(kwargs) or "The changed factor affects the linked evidence. This is illustrative rather than predictive. No investment advice is provided.",
    )
    monkeypatch.setattr("app.core.edgar_client.get_filings_near_date", lambda *args: [])
    monkeypatch.setattr("app.core.finnhub_client.company_news", lambda *args: [])
    scenario_cache = {}
    monkeypatch.setattr("app.core.cache.cache_get", lambda key: scenario_cache.get(key))
    monkeypatch.setattr("app.core.cache.cache_set", lambda key, value, ttl: scenario_cache.__setitem__(key, value))

    with TestClient(app) as client:
        simulated = client.post("/api/simulate", json={"run_id": ctx.run_id, "usd_pct": 20})
        precedents = client.get(
            "/api/precedents",
            params={"ticker": "NVDA", "event_type": "AI competitive shock", "as_of": "2025-01-28"},
        )
        unusual = client.get(
            f"/api/cards/C5/unusual-days?run_id={ctx.run_id}",
        )
        explained = client.post(
            "/api/explain-day",
            json={"run_id": ctx.run_id, "card_id": "C5", "event_date": "2025-01-15"},
        )
        explained_again = client.post(
            "/api/explain-day",
            json={"run_id": ctx.run_id, "card_id": "C5", "event_date": "2025-01-15"},
        )

    assert simulated.status_code == 200
    assert simulated.json()["scenario"]["composite_signal"] > simulated.json()["baseline"]["composite_signal"]
    assert not llm_calls
    assert "presentation" in simulated.json()
    assert precedents.status_code == 200
    assert len(precedents.json()["matches"]) == 5
    assert all(match["source"]["url"].startswith("https://www.sec.gov/") for match in precedents.json()["matches"])
    assert unusual.status_code == 200
    assert [day["date"] for day in unusual.json()["days"]] == ["2025-01-15"]
    assert explained.status_code == 200
    assert explained.json()["used_llm"] is False
    assert explained.json()["classification"] in {"company_led", "sector_led", "market_led"}
    assert len(explained.json()["citations"]) == 3
    assert explained_again.json()["cached"] is True


def test_scenario_explanation_is_cached_by_run_and_overrides(monkeypatch):
    from fastapi.testclient import TestClient

    from app.core.events import RunContext
    from app.core.run_store import put
    from app.main import app

    ctx = RunContext(run_id="scenario-explanation-cache-test", ticker="INTC")
    ctx.cards["C1"] = _card("C1", 0.1)
    ctx.aggregate = AggregateResult(
        composite_signal=0.1,
        evidence_strength=0.4,
        coverage=1,
        scenarios=[],
        card_contributions={"C1": 0.1},
    )
    put(ctx)
    llm_calls = []
    monkeypatch.setattr(
        "app.core.config.get_settings",
        lambda: type("Settings", (), {"llm_api_key": "configured"})(),
    )
    monkeypatch.setattr(
        "app.llm.client.chat_completion",
        lambda **kwargs: llm_calls.append(kwargs) or "The changed factor affects the linked evidence. This is illustrative rather than predictive. No investment advice is provided.",
    )
    cache = {}
    monkeypatch.setattr("app.core.cache.cache_get", lambda key: cache.get(key))
    monkeypatch.setattr("app.core.cache.cache_set", lambda key, value, ttl: cache.__setitem__(key, value))

    with TestClient(app) as client:
        body = {"run_id": ctx.run_id, "usd_pct": 10}
        first = client.post("/api/simulate/explain", json=body)
        second = client.post("/api/simulate/explain", json=body)

    assert first.status_code == 200
    assert first.json()["used_llm"] is True
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert len(llm_calls) == 1


def test_fixture_explanation_uses_curated_evidence_without_external_calls(monkeypatch):
    from fastapi.testclient import TestClient

    from app.core.events import RunContext
    from app.core.run_store import put
    from app.main import app

    ctx = RunContext(run_id="fixture-explanation-no-network", ticker="INTC", is_fixture=True)
    ctx.cards["C5"] = _card("C5", 0.1)
    ctx.cards["C1"] = _card("C1", 0.1)
    ctx.aggregate = AggregateResult(
        composite_signal=0.1,
        evidence_strength=0.4,
        coverage=1,
        scenarios=[],
        card_contributions={"C1": 0.1},
    )
    ctx.event_evidence = {
        "markers": {
            "C5": [{
                "date": "2024-12-02",
                "adjusted_price": 25.0,
                "daily_percentage_move": 2.5,
                "robust_score": 4.1,
            }]
        },
        "explanations": {
            "2024-12-02": {
                "explanation": (
                    "The stock price moved on the selected date [1]. "
                    "The source describes the related company event [1]. "
                    "This comparison does not establish a cause."
                ),
                "classification": "company_led",
                "citations": [{
                    "number": 1,
                    "title": "Company event filing",
                    "url": "https://www.sec.gov/Archives/edgar/data/1/1/event.htm",
                    "date": "2024-12-02",
                    "type": "sec_filing",
                }],
            }
        },
    }
    put(ctx)

    def forbidden(*args, **kwargs):
        raise AssertionError("fixture explanation must not make external calls")

    monkeypatch.setattr("app.core.edgar_client.get_filings_near_date", forbidden)
    monkeypatch.setattr("app.core.finnhub_client.company_news", forbidden)
    monkeypatch.setattr("app.llm.client.chat_completion", forbidden)
    monkeypatch.setattr(
        "app.core.config.get_settings",
        lambda: type("Settings", (), {"llm_api_key": "configured"})(),
    )
    cache = {}
    monkeypatch.setattr("app.core.cache.cache_get", lambda key: cache.get(key))
    monkeypatch.setattr("app.core.cache.cache_set", lambda key, value, ttl: cache.__setitem__(key, value))

    with TestClient(app) as client:
        markers = client.get(f"/api/cards/C5/unusual-days?run_id={ctx.run_id}")
        explanation = client.post(
            "/api/explain-day",
            json={"run_id": ctx.run_id, "card_id": "C5", "event_date": "2024-12-02"},
        )
        scenario = client.post(
            "/api/simulate/explain",
            json={"run_id": ctx.run_id, "usd_pct": 10},
        )

    assert markers.json()["days"][0]["date"] == "2024-12-02"
    assert explanation.status_code == 200
    assert explanation.json()["used_llm"] is False
    assert explanation.json()["citations"][0]["title"] == "Company event filing"
    assert scenario.status_code == 200
    assert scenario.json()["used_llm"] is False


def test_finnhub_news_is_optional_filtered_and_cached(monkeypatch):
    from app.core import finnhub_client

    cache = {}
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return [
                {
                    "headline": "Company update",
                    "url": "https://news.example.org/company-update",
                    "source": "Example News",
                    "datetime": 1733184000,
                    "summary": "Dated report.",
                },
                {"headline": "bad URL", "url": "http://invalid.example.org", "datetime": 1733184000},
            ]

    monkeypatch.setattr(
        finnhub_client,
        "get_settings",
        lambda: type("Settings", (), {"finnhub_api_key": "test-key"})(),
    )
    monkeypatch.setattr(finnhub_client, "cache_get", lambda key: cache.get(key))
    monkeypatch.setattr(
        finnhub_client,
        "cache_set",
        lambda key, value, ttl: cache.__setitem__(key, value),
    )
    monkeypatch.setattr(
        finnhub_client.httpx,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs)) or Response(),
    )

    first = finnhub_client.company_news("INTC", "2024-12-02")
    second = finnhub_client.company_news("INTC", "2024-12-02")

    assert len(calls) == 1
    assert first == second
    assert [item["title"] for item in first] == ["Company update"]
    assert calls[0][1]["params"]["symbol"] == "INTC"


def test_llm_day_explanation_rejects_unknown_citations():
    from app.api.analyze import _valid_cited_explanation

    assert _valid_cited_explanation(
        "The stock moved sharply [1]. The sector also changed [1]. "
        "These moves do not prove a cause.",
        1,
    )
    assert not _valid_cited_explanation(
        "The stock moved sharply [2]. The sector also changed [1]. "
        "These moves do not prove a cause.",
        1,
    )


def test_fixture_replay_replaces_the_recorded_done_run_id(monkeypatch):
    """Replay-only endpoints must use the current request's run ID."""
    from app.core import fixture_engine
    from app.core.events import RunContext

    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(fixture_engine.asyncio, "sleep", no_sleep)

    async def collect_events():
        ctx = RunContext(
            run_id="new-fixture-run-id",
            ticker="INTC",
            as_of="2024-12-02",
        )
        events = []
        async for chunk in fixture_engine.replay_fixture(
            fixture_engine.FIXTURE_DIR / "intc_2024_12_02.json",
            ctx,
        ):
            events.append(json.loads(chunk.removeprefix("data: ").strip()))
        return ctx, events

    ctx, events = asyncio.run(collect_events())
    done = next(event for event in events if event["type"] == "done")

    assert done["run_id"] == ctx.run_id
    assert done["data"]["run_id"] == ctx.run_id


def test_demo_fixtures_include_clickable_c5_evidence():
    from pathlib import Path

    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures"
    names = (
        "intc_2024_12_02.json",
        "jpm_2023_03_13.json",
        "xom_2022_02_25.json",
        "nvda_2025_01_28.json",
    )
    for name in names:
        raw = json.loads((fixture_dir / name).read_text())
        evidence = raw["meta"]["event_evidence"]
        assert evidence["markers"]["C5"]
        marker_date = evidence["markers"]["C5"][0]["date"]
        assert evidence["explanations"][marker_date]["citations"]
        c5 = next(
            event["data"]["card"] for event in raw["events"]
            if event["type"] == "card_done" and event["data"]["card"]["id"] == "C5"
        )
        assert len(c5["series"]) >= 10
        assert set(c5["related_series"]) == {"stock", "sector", "market"}


def _precedent_record(record_id: str, ticker: str, event_day: int) -> dict:
    from datetime import date, timedelta

    start = date(2020, 1, 2) + timedelta(days=event_day)
    trading_dates = []
    current = start
    while len(trading_dates) < 61:
        if current.weekday() < 5:
            trading_dates.append(current.isoformat())
        current += timedelta(days=1)
    series = [
        {"day": day, "date": trading_dates[day], "value": round(100 + day * 0.1, 6)}
        for day in range(61)
    ]
    return {
        "id": record_id,
        "event_date": start.isoformat(),
        "ticker": ticker,
        "sector": "technology",
        "sector_etf": "XLK",
        "event_type": "Earnings update",
        "category": "earnings",
        "market_mood": "mixed",
        "summary": "The issuer reported a material update in its filed current report.",
        "source": {
            "title": "SEC Form 8-K filed with the issuer's current report",
            "url": f"https://www.sec.gov/Archives/edgar/data/1/{record_id}/filing.htm",
        },
        "outcomes": {
            "returns": {
                entity: {"d5": 0.5, "d20": 2.0, "d60": 6.0}
                for entity in ("stock", "sector", "spy")
            },
            "series": {entity: series for entity in ("stock", "sector", "spy")},
        },
    }


def test_precedent_validator_requires_complete_unique_and_covered_data():
    from datetime import date

    import pytest

    from app.precedents.schema import SUPPORTED_TICKERS
    from scripts.validate_precedents import validate_dataset

    rows = [
        _precedent_record(f"record-{ticker.lower()}-{index}", ticker, index)
        for ticker in sorted(SUPPORTED_TICKERS)
        for index in range(7)
    ]
    assert len(validate_dataset(rows, date(2021, 1, 1))) == 105

    with pytest.raises(ValueError, match="duplicate precedent IDs"):
        validate_dataset(rows + [rows[0]], date(2021, 1, 1))

    rows[0]["outcomes"]["series"]["stock"].pop()
    with pytest.raises(ValueError, match="trading days 0 through 60"):
        validate_dataset(rows, date(2021, 1, 1))


def test_precedent_validator_rejects_placeholder_sources_and_future_windows():
    from datetime import date

    import pytest

    from scripts.validate_precedents import validate_dataset

    row = _precedent_record("verified-test", "NVDA", 0)
    row["source"] = {"title": "Placeholder source", "url": "https://example.com/event"}
    with pytest.raises(ValueError, match="placeholder"):
        validate_dataset([row], date(2021, 1, 1), require_minimum=False)

    row = _precedent_record("future-window-test", "NVDA", 0)
    with pytest.raises(ValueError, match="not complete"):
        validate_dataset([row], date(2020, 3, 1), require_minimum=False)


def test_precedent_ranking_returns_five_deterministic_completed_matches(tmp_path, monkeypatch):
    import json
    from datetime import date

    from app.precedents import engine

    rows = [
        _precedent_record(f"nvda-{index}", "NVDA", index)
        for index in range(6)
    ]
    rows.extend(_precedent_record(f"msft-{index}", "MSFT", index) for index in range(2))
    for row in rows:
        row["category"] = "technology"
        row["market_mood"] = "mixed"

    data_path = tmp_path / "precedents.json"
    data_path.write_text(json.dumps(rows))
    monkeypatch.setattr(engine, "DATA_PATH", data_path)

    matches = engine.find_precedents("NVDA", "AI competitive shock", "2020-06-01")
    assert len(matches) == 5
    assert all(item["ticker"] == "NVDA" for item in matches)
    assert all(item["outcomes"]["series"]["stock"][-1]["date"] < "2020-06-01" for item in matches)
    assert matches == engine.find_precedents("NVDA", "AI competitive shock", "2020-06-01")

    future = engine.find_precedents("NVDA", "AI competitive shock", "2020-02-01")
    assert future == []
