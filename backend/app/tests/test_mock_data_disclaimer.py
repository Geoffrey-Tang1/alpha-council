def test_analysis_response_includes_mock_data_disclaimer(client):
    response = client.post(
        "/api/v1/analysis/run",
        json={
            "ticker": "NVDA",
            "market": "US",
            "time_horizon": "swing",
            "strategy_preference": "moving_average_crossover",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data_provider"] == "mock"
    assert body["data_disclaimer"] == "MVP Mode: using deterministic mock data. Not real market data."
    assert body["data_quality"] == "MOCK"
    assert "MVP Mode: using deterministic mock data. Not real market data." in body["data_warnings"]
    assert "agent_outputs" in body
    assert "technical_analysis" in body["agent_outputs"]
