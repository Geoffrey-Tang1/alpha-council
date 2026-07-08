import json
from datetime import datetime, timezone
from uuid import uuid4

from app.db.database import get_connection


def test_analysis_endpoint_returns_structured_saved_decision(client):
    payload = {
        "ticker": "NVDA",
        "market": "US",
        "time_horizon": "swing",
        "strategy_preference": "moving_average_crossover",
    }

    response = client.post("/api/v1/analysis/run", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["decision_id"].startswith("dec_")
    assert body["ticker"] == "NVDA"
    assert body["company_name"] == "NVIDIA Corporation"
    assert body["normalized_ticker"] == "NVDA"
    assert body["display_symbol"] == "NVDA"
    assert body["market"] == "US"
    assert body["decision"] in {"BUY", "SELL", "HOLD", "WATCH", "AVOID"}
    assert 0 <= body["confidence"] <= 1
    assert body["saved"] is True
    assert body["bull_case"]["bull_points"]
    assert body["bear_case"]["bear_points"]
    assert body["agent_votes"]
    assert body["agent_outputs"]["risk_manager"]["risk_warnings"]
    assert body["data_provider"] == "mock"
    assert body["data_quality"] == "MOCK"
    assert body["data_disclaimer"] == "MVP Mode: using deterministic mock data. Not real market data."
    assert body["data_warnings"]
    assert body["data_sources"][0]["name"] == "mock"


def test_analysis_saves_decision_for_history(client):
    payload = {
        "ticker": "TSM",
        "market": "TW",
        "time_horizon": "medium_term",
        "strategy_preference": "rsi_oversold_rebound",
    }
    run_response = client.post("/api/v1/analysis/run", json=payload)
    assert run_response.status_code == 200
    decision_id = run_response.json()["decision_id"]

    history_response = client.get("/api/v1/decisions")

    assert history_response.status_code == 200
    history = history_response.json()
    assert history["total"] >= 1
    assert any(item["decision_id"] == decision_id for item in history["items"])


def test_legacy_saved_decision_without_instrument_metadata_loads_safely(client):
    run_response = client.post(
        "/api/v1/analysis/run",
        json={
            "ticker": "AAPL",
            "market": "US",
            "time_horizon": "swing",
            "strategy_preference": "moving_average_crossover",
        },
    )
    assert run_response.status_code == 200
    payload = run_response.json()
    for key in ["company_name", "normalized_ticker", "display_symbol"]:
        payload.pop(key, None)
    payload["decision_id"] = f"dec_legacy_{uuid4().hex}"
    payload["timestamp"] = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO decisions (
                decision_id,
                timestamp,
                ticker,
                market,
                latest_price,
                market_status,
                final_decision,
                confidence,
                time_horizon,
                full_payload_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["decision_id"],
                payload["timestamp"],
                payload["ticker"],
                payload["market"],
                payload["latest_price"],
                payload["market_status"],
                payload["decision"],
                payload["confidence"],
                payload["time_horizon"],
                json.dumps(payload),
                payload["timestamp"],
            ),
        )
        connection.commit()

    detail_response = client.get(f"/api/v1/decisions/{payload['decision_id']}")

    assert detail_response.status_code == 200
    body = detail_response.json()
    assert body["company_name"] == "Apple Inc."
    assert body["normalized_ticker"] == "AAPL"
    assert body["display_symbol"] == "AAPL"
