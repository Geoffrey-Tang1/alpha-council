from pathlib import Path

from app.llm.provider_registry import get_llm_provider
from app.llm.settings_store import mask_api_key


def test_get_llm_settings_returns_safe_defaults_without_key(client):
    response = client.get("/api/v1/llm/settings")

    assert response.status_code == 200
    body = response.json()
    assert body["llm_provider"] == "disabled"
    assert body["enable_llm_reasoning"] is False
    assert body["selected_model"] == "none"
    assert body["api_key_present"] is False
    assert body["masked_api_key"] is None
    assert "api_key" not in body


def test_patch_llm_settings_saves_provider_model_and_masks_api_key(client):
    response = client.patch(
        "/api/v1/llm/settings",
        json={
            "llm_provider": "openai",
            "enable_llm_reasoning": True,
            "selected_model": "gpt-4.1-mini",
            "api_key": "sk-test-secret-abcd",
            "temperature": 0.3,
            "max_tokens": 1600,
            "timeout_seconds": 45,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["llm_provider"] == "openai"
    assert body["enable_llm_reasoning"] is True
    assert body["selected_model"] == "gpt-4.1-mini"
    assert body["api_key_present"] is True
    assert body["masked_api_key"] == "sk-****abcd"
    assert "sk-test-secret-abcd" not in str(body)
    assert body["temperature"] == 0.3
    assert body["max_tokens"] == 1600
    assert body["timeout_seconds"] == 45


def test_omitted_api_key_keeps_existing_key_and_empty_string_clears(client):
    client.patch(
        "/api/v1/llm/settings",
        json={
            "llm_provider": "openai",
            "enable_llm_reasoning": True,
            "selected_model": "gpt-4o",
            "api_key": "sk-keep-me-1234",
        },
    )

    kept_response = client.patch(
        "/api/v1/llm/settings",
        json={
            "llm_provider": "openai",
            "selected_model": "gpt-4.1-mini",
        },
    )
    cleared_response = client.patch("/api/v1/llm/settings", json={"api_key": ""})

    assert kept_response.status_code == 200
    assert kept_response.json()["masked_api_key"] == "sk-****1234"
    assert cleared_response.status_code == 200
    assert cleared_response.json()["api_key_present"] is False
    assert cleared_response.json()["masked_api_key"] is None


def test_mock_connection_test_succeeds_and_updates_settings(client):
    response = client.post(
        "/api/v1/llm/test",
        json={
            "llm_provider": "mock",
            "selected_model": "mock-llm-v1",
            "api_key": None,
            "base_url": None,
        },
    )
    settings_response = client.get("/api/v1/llm/settings")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["provider"] == "mock"
    assert body["message"] == "Mock LLM provider is available."
    assert body["latency_ms"] >= 1
    assert settings_response.json()["last_connection_status"] == "success"


def test_provider_change_resets_stale_connection_status(client):
    client.post(
        "/api/v1/llm/test",
        json={
            "llm_provider": "mock",
            "selected_model": "mock-llm-v1",
            "api_key": None,
            "base_url": None,
        },
    )

    response = client.patch(
        "/api/v1/llm/settings",
        json={
            "llm_provider": "disabled",
            "enable_llm_reasoning": False,
            "selected_model": "none",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["llm_provider"] == "disabled"
    assert body["last_connection_status"] == "not_tested"
    assert body["last_connection_message"] == "Connection has not been tested."


def test_disabled_connection_test_returns_clear_message(client):
    response = client.post(
        "/api/v1/llm/test",
        json={
            "llm_provider": "disabled",
            "selected_model": "none",
            "api_key": None,
            "base_url": None,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "LLM provider is disabled."


def test_real_provider_missing_key_is_safe_and_status_reflects_settings(client):
    client.patch(
        "/api/v1/llm/settings",
        json={
            "llm_provider": "openrouter",
            "enable_llm_reasoning": True,
            "selected_model": "openrouter/auto",
            "api_key": "",
        },
    )

    status_response = client.get("/api/v1/llm/status")
    analysis_response = client.post(
        "/api/v1/analysis/run",
        json={
            "ticker": "NVDA",
            "market": "US",
            "time_horizon": "swing",
            "strategy_preference": "moving_average_crossover",
        },
    )

    assert status_response.status_code == 200
    status = status_response.json()
    assert status["llm_provider"] == "openrouter"
    assert status["enabled"] is False
    assert "API key is missing" in status["warnings"][0]

    assert analysis_response.status_code == 200
    decision = analysis_response.json()
    assert decision["llm_provider"] == "openrouter"
    assert decision["llm_used"] is False
    assert decision["decision"] != "BUY"


def test_provider_registry_uses_saved_settings(client):
    client.patch(
        "/api/v1/llm/settings",
        json={
            "llm_provider": "mock",
            "enable_llm_reasoning": True,
            "selected_model": "mock-llm-v1",
        },
    )

    provider = get_llm_provider()

    assert provider.provider_name == "mock"
    assert provider.enabled is True


def test_settings_file_is_created_locally(client, monkeypatch):
    settings_path = Path("test_llm_settings.local.json")
    assert not settings_path.exists()

    response = client.patch(
        "/api/v1/llm/settings",
        json={"llm_provider": "mock", "enable_llm_reasoning": True},
    )

    assert response.status_code == 200
    assert settings_path.exists()


def test_mask_api_key_examples():
    assert mask_api_key("sk-test-secret-abcd") == "sk-****abcd"
    assert mask_api_key("claude-secret-wxyz") == "claude-****wxyz"
    assert mask_api_key("key-secret-1234") == "key-****1234"
