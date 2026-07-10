import json
from datetime import datetime, timezone
from uuid import uuid4

from app.db.database import get_connection
from app.schemas.research import RESEARCH_SCHEMA_VERSION


def _analysis_payload(**overrides):
    payload = {
        "ticker": "NVDA",
        "market": "US",
        "time_horizon": "swing",
        "strategy_preference": "moving_average_crossover",
        "research_objective": "investment_thesis",
        "user_thesis": "Demand may improve, but valuation needs discipline.",
        "user_concerns": ["valuation risk", "earnings event risk"],
        "locale": "en",
    }
    payload.update(overrides)
    return payload


def test_analysis_response_includes_structured_research_report(client):
    response = client.post("/api/v1/analysis/run", json=_analysis_payload())

    assert response.status_code == 200
    body = response.json()
    report = body["research_report"]
    assert report["schema_version"] == RESEARCH_SCHEMA_VERSION
    assert report["request"]["ticker"] == "NVDA"
    assert report["request"]["strategy"] == "moving_average_crossover"
    assert report["request"]["investment_horizon"] == "swing"
    assert report["request"]["research_objective"] == "investment_thesis"
    assert report["request"]["user_thesis"] == "Demand may improve, but valuation needs discipline."
    assert report["request"]["user_concerns"] == ["valuation risk", "earnings event risk"]
    assert report["execution_status"] in {"completed", "partial_success"}
    assert report["research_plan"]["dimensions"]
    assert report["evidence"]
    assert report["specialist_outputs"]
    assert report["investment_thesis"]["executive_summary"]
    assert report["risk_review"]["risks"]
    assert report["confidence_assessment"]["methodology"]
    assert report["committee_decision"]["decision"] == body["decision"]


def test_research_report_marks_unavailable_dimensions_and_sources_honestly(client):
    response = client.post("/api/v1/analysis/run", json=_analysis_payload())

    assert response.status_code == 200
    report = response.json()["research_report"]
    unavailable = {
        item["title"]: item
        for item in report["evidence"]
        if item["availability_status"] == "unavailable"
    }
    assert "Latest filing" in unavailable
    assert "Verified news feed" in unavailable
    assert unavailable["Latest filing"]["source_type"] == "unavailable_source"
    assert unavailable["Latest filing"]["source_reference"] is None
    assert report["missing_information"]
    assert "valuation" in report["data_quality_summary"]["unavailable_dimensions"]
    assert not any("http" in str(item.get("source_reference")) for item in report["evidence"])


def test_research_report_bull_and_bear_cases_are_separate(client):
    response = client.post("/api/v1/analysis/run", json=_analysis_payload())

    assert response.status_code == 200
    thesis = response.json()["research_report"]["investment_thesis"]
    bull = thesis["bull_case"]
    bear = thesis["bear_case"]
    assert bull["core_argument"] != bear["core_argument"]
    assert bull["evidence_references"]
    assert bear["evidence_references"]
    assert bull["supporting_factors"]
    assert bear["supporting_factors"]


def test_research_confidence_penalizes_mock_and_missing_information(client):
    response = client.post("/api/v1/analysis/run", json=_analysis_payload())

    assert response.status_code == 200
    report = response.json()["research_report"]
    confidence = report["confidence_assessment"]
    assert confidence["level"] in {"low", "medium"}
    assert confidence["score"] < 0.7
    assert any("Mock data" in penalty for penalty in confidence["confidence_penalties"])
    assert report["data_quality_summary"]["overall_completeness"] in {"limited", "partial"}


def test_structured_research_report_is_persisted_with_decision(client):
    response = client.post("/api/v1/analysis/run", json=_analysis_payload(ticker="AAPL"))

    assert response.status_code == 200
    decision_id = response.json()["decision_id"]
    detail_response = client.get(f"/api/v1/decisions/{decision_id}")

    assert detail_response.status_code == 200
    persisted = detail_response.json()
    assert persisted["research_report"]["schema_version"] == RESEARCH_SCHEMA_VERSION
    assert persisted["research_report"]["request"]["ticker"] == "AAPL"


def test_legacy_decision_without_research_report_loads_safely(client):
    response = client.post("/api/v1/analysis/run", json=_analysis_payload(ticker="MSFT"))
    assert response.status_code == 200
    payload = response.json()
    payload.pop("research_report", None)
    payload["decision_id"] = f"dec_legacy_research_{uuid4().hex}"
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
    assert detail_response.json()["research_report"] is None


def test_analysis_request_validation_rejects_invalid_strategy(client):
    response = client.post(
        "/api/v1/analysis/run",
        json=_analysis_payload(strategy_preference="unsupported_strategy"),
    )

    assert response.status_code == 422


def test_mock_llm_outputs_are_labeled_as_model_inference_evidence(client):
    settings_response = client.patch(
        "/api/v1/llm/settings",
        json={
            "llm_provider": "mock",
            "enable_llm_reasoning": True,
            "selected_model": "mock-llm-v1",
        },
    )
    assert settings_response.status_code == 200

    response = client.post("/api/v1/analysis/run", json=_analysis_payload(ticker="TSLA"))

    assert response.status_code == 200
    body = response.json()
    assert body["llm_used"] is True
    llm_evidence = [
        item
        for item in body["research_report"]["evidence"]
        if item["category"] == "model_reasoning"
    ]
    assert llm_evidence
    assert {item["source_type"] for item in llm_evidence} == {"model_inference"}
    assert {item["evidence_kind"] for item in llm_evidence} == {"model_inference"}
