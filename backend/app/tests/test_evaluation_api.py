from app.schemas.evaluations import EVALUATION_DISCLAIMER


def test_evaluation_api_response_shape_and_summary(client):
    analysis_payload = {
        "ticker": "NVDA",
        "market": "US",
        "time_horizon": "swing",
        "strategy_preference": "moving_average_crossover",
    }
    decision_response = client.post("/api/v1/analysis/run", json=analysis_payload)
    assert decision_response.status_code == 200
    decision_id = decision_response.json()["decision_id"]

    evaluation_response = client.post(f"/api/v1/evaluations/decision/{decision_id}")

    assert evaluation_response.status_code == 200
    evaluation = evaluation_response.json()
    assert evaluation["evaluation_id"].startswith("eval_")
    assert evaluation["decision_id"] == decision_id
    assert evaluation["ticker"] == "NVDA"
    assert evaluation["company_name"] == "NVIDIA Corporation"
    assert evaluation["normalized_ticker"] == "NVDA"
    assert evaluation["display_symbol"] == "NVDA"
    assert evaluation["market"] == "US"
    assert evaluation["evaluation_status"] in {"EVALUATED", "INSUFFICIENT_DATA", "ERROR"}
    assert evaluation["directional_result"] in {
        "FAVORABLE",
        "UNFAVORABLE",
        "NEUTRAL_MONITORING",
        "NEUTRAL_HOLD",
        "MISSED_UPSIDE",
        "INSUFFICIENT_DATA",
        "UNKNOWN",
    }
    assert evaluation["data_provider"] == "mock"
    assert evaluation["data_quality"] == "MOCK"
    assert evaluation["data_disclaimer"] == "MVP Mode: using deterministic mock data. Not real market data."
    assert evaluation["evaluation_disclaimer"] == EVALUATION_DISCLAIMER

    list_response = client.get("/api/v1/evaluations", params={"ticker": "NVDA", "limit": 20})
    assert list_response.status_code == 200
    listed = list_response.json()
    assert listed["total"] >= 1
    assert any(item["evaluation_id"] == evaluation["evaluation_id"] for item in listed["items"])

    detail_response = client.get(f"/api/v1/evaluations/{evaluation['evaluation_id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["evaluation_id"] == evaluation["evaluation_id"]
    assert detail["company_name"] == "NVIDIA Corporation"

    summary_response = client.get("/api/v1/evaluations/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_evaluated"] >= 1
    assert summary["disclaimer"] == EVALUATION_DISCLAIMER
    assert "average_forward_return_by_decision" in summary


def test_evaluation_run_skips_already_evaluated_decisions(client):
    analysis_payload = {
        "ticker": "AAPL",
        "market": "US",
        "time_horizon": "swing",
        "strategy_preference": "moving_average_crossover",
    }
    decision_response = client.post("/api/v1/analysis/run", json=analysis_payload)
    assert decision_response.status_code == 200

    first_run = client.post("/api/v1/evaluations/run", json={"limit": 20, "include_already_evaluated": False})
    assert first_run.status_code == 200

    second_run = client.post("/api/v1/evaluations/run", json={"limit": 20, "include_already_evaluated": False})
    assert second_run.status_code == 200
    assert second_run.json()["skipped_count"] >= 1
