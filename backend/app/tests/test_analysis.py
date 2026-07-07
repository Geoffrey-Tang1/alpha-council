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
