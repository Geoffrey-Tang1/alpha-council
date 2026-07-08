from app.llm.mock_provider import MockLLMProvider
from app.llm.provider_registry import get_llm_provider


ANALYSIS_PAYLOAD = {
    "ticker": "NVDA",
    "market": "US",
    "time_horizon": "swing",
    "strategy_preference": "moving_average_crossover",
}


def test_llm_disabled_mode_returns_disabled_fields(client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "disabled")
    monkeypatch.setenv("ENABLE_LLM_REASONING", "false")

    response = client.post("/api/v1/analysis/run", json=ANALYSIS_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["llm_enabled"] is False
    assert body["llm_provider"] == "disabled"
    assert body["llm_used"] is False
    assert "LLM reasoning disabled" in body["llm_warnings"][0]


def test_mock_llm_provider_returns_deterministic_outputs(client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("ENABLE_LLM_REASONING", "true")

    response = client.post("/api/v1/analysis/run", json=ANALYSIS_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["llm_enabled"] is True
    assert body["llm_provider"] == "mock"
    assert body["llm_used"] is True
    assert "Mock LLM provider active" in body["llm_warnings"][0]
    assert "mock LLM memo" in body["llm_outputs"]["decision_memo"]["summary"]
    assert body["llm_outputs"]["decision_memo"]["provider"] == "mock"
    assert body["llm_outputs"]["decision_memo"]["prompt_name"] == "decision_memo_v1"
    assert body["llm_outputs"]["prompt_versions"]["decision_memo_v1"] == "v1"


def test_openai_missing_api_key_falls_back_without_external_call(client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("ENABLE_LLM_REASONING", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    status_response = client.get("/api/v1/llm/status")
    analysis_response = client.post("/api/v1/analysis/run", json=ANALYSIS_PAYLOAD)

    assert status_response.status_code == 200
    status = status_response.json()
    assert status["llm_provider"] == "openai"
    assert status["enabled"] is False
    assert status["available"] is False
    assert "OPENAI_API_KEY is missing" in status["warnings"][0]

    assert analysis_response.status_code == 200
    body = analysis_response.json()
    assert body["llm_enabled"] is False
    assert body["llm_provider"] == "openai"
    assert body["llm_used"] is False
    assert "OPENAI_API_KEY is missing" in body["llm_warnings"][0]


def test_provider_registry_selects_mock_llm(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("ENABLE_LLM_REASONING", "true")

    provider = get_llm_provider()

    assert isinstance(provider, MockLLMProvider)
    assert provider.enabled is True
    assert provider.available is True


def test_llm_cannot_override_risk_veto_or_final_decision(client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("ENABLE_LLM_REASONING", "true")

    response = client.post("/api/v1/analysis/run", json=ANALYSIS_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["agent_outputs"]["risk_manager"]["veto"] is True
    assert body["decision"] != "BUY"
    assert body["llm_used"] is True
    assert "BUY is blocked while using MOCK data." in body["agent_outputs"]["risk_manager"]["veto_reason"]
    assert "Risk Manager veto" in body["llm_outputs"]["decision_memo"]["summary"]


def test_llm_status_endpoint_disabled_by_default(client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "disabled")
    monkeypatch.setenv("ENABLE_LLM_REASONING", "false")

    response = client.get("/api/v1/llm/status")

    assert response.status_code == 200
    body = response.json()
    assert body["llm_provider"] == "disabled"
    assert body["enabled"] is False
    assert body["available"] is False
