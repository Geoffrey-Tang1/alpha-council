from app.backtesting.engine import HISTORICAL_SIMULATION_WARNING


def test_backtest_api_response_shape_and_persistence(client):
    payload = {
        "ticker": "NVDA",
        "market": "US",
        "start_date": "2023-01-01",
        "end_date": "2024-12-31",
        "strategy_name": "moving_average_crossover",
        "initial_capital": 100000,
        "transaction_cost_bps": 5,
        "slippage_bps": 10,
    }

    run_response = client.post("/api/v1/backtests/run", json=payload)

    assert run_response.status_code == 200
    body = run_response.json()
    assert body["backtest_id"].startswith("bt_")
    assert body["ticker"] == "NVDA"
    assert body["company_name"] == "NVIDIA Corporation"
    assert body["normalized_ticker"] == "NVDA"
    assert body["display_symbol"] == "NVDA"
    assert body["market"] == "US"
    assert body["strategy_name"] == "moving_average_crossover"
    assert body["initial_capital"] == 100000
    assert "total_return" in body
    assert "cagr" in body
    assert "max_drawdown" in body
    assert "win_rate" in body
    assert "number_of_trades" in body
    assert "average_trade_return" in body
    assert body["equity_curve"]
    assert isinstance(body["trade_log"], list)
    assert body["data_provider"] == "mock"
    assert body["data_quality"] == "MOCK"
    assert body["data_disclaimer"] == "MVP Mode: using deterministic mock data. Not real market data."
    assert HISTORICAL_SIMULATION_WARNING in body["warning"]

    list_response = client.get("/api/v1/backtests")
    assert list_response.status_code == 200
    history = list_response.json()
    assert history["total"] >= 1
    assert any(item["backtest_id"] == body["backtest_id"] for item in history["items"])

    detail_response = client.get(f"/api/v1/backtests/{body['backtest_id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["backtest_id"] == body["backtest_id"]
    assert detail["company_name"] == "NVIDIA Corporation"
