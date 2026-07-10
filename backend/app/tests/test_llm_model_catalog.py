import json
from pathlib import Path


def test_get_models_disabled_returns_static_empty_list(client):
    response = client.get("/api/v1/llm/models", params={"provider": "disabled"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "disabled"
    assert body["models"] == []
    assert body["source"] == "static"
    assert body["status"] == "disabled"
    assert body["supports_refresh"] is False


def test_get_models_mock_returns_static_mock_model(client):
    response = client.get("/api/v1/llm/models", params={"provider": "mock"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["models"][0]["id"] == "mock-llm-v1"
    assert body["models"][0]["source"] == "static"
    assert body["status"] == "static"


def test_get_models_openai_without_cache_returns_static_fallback(client):
    response = client.get("/api/v1/llm/models", params={"provider": "openai"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openai"
    assert body["source"] == "static"
    assert body["status"] == "static"
    assert "gpt-5.4-mini" in [model["id"] for model in body["models"]]
    assert body["supports_refresh"] is True


def test_refresh_openai_missing_key_returns_fallback_without_crashing(client):
    client.patch(
        "/api/v1/llm/settings",
        json={
            "llm_provider": "openai",
            "enable_llm_reasoning": True,
            "selected_model": "gpt-5.4-mini",
            "api_key": "",
        },
    )

    response = client.post("/api/v1/llm/models/refresh", json={"provider": "openai"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openai"
    assert body["source"] == "static"
    assert body["status"] == "missing_api_key"
    assert "API key is required" in body["message"]
    assert "gpt-5.4-mini" in [model["id"] for model in body["models"]]


def test_refresh_mock_returns_static_success(client):
    response = client.post("/api/v1/llm/models/refresh", json={"provider": "mock"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["source"] == "static"
    assert body["status"] == "static"
    assert body["models"] == [{"id": "mock-llm-v1", "name": "mock-llm-v1", "source": "static", "created": None, "metadata": {}}]


def test_refresh_writes_cache_and_get_reads_without_api_key(client, monkeypatch):
    import app.llm.model_catalog as model_catalog

    def fake_fetch(provider, api_key, base_url, timeout_seconds):
        assert provider == "openai"
        assert api_key == "sk-test-secret-abcd"
        return [
            {"id": "gpt-live-test", "name": "gpt-live-test", "created": None, "metadata": {"owned_by": "test"}}
        ]

    monkeypatch.setattr(model_catalog, "_fetch_live_models", fake_fetch)
    client.patch(
        "/api/v1/llm/settings",
        json={
            "llm_provider": "openai",
            "enable_llm_reasoning": True,
            "selected_model": "gpt-live-test",
            "api_key": "sk-test-secret-abcd",
        },
    )

    refresh_response = client.post("/api/v1/llm/models/refresh", json={"provider": "openai"})
    get_response = client.get("/api/v1/llm/models", params={"provider": "openai"})
    cache_payload = json.loads(Path("test_model_catalog_cache.local.json").read_text())

    assert refresh_response.status_code == 200
    assert refresh_response.json()["source"] == "live"
    assert refresh_response.json()["models"][0]["id"] == "gpt-live-test"
    assert get_response.status_code == 200
    assert get_response.json()["source"] == "cache"
    assert get_response.json()["models"][0]["source"] == "cache"
    assert "sk-test-secret-abcd" not in str(refresh_response.json())
    assert "sk-test-secret-abcd" not in str(get_response.json())
    assert "sk-test-secret-abcd" not in json.dumps(cache_payload)


def test_unknown_provider_returns_validation_error(client):
    response = client.get("/api/v1/llm/models", params={"provider": "not_real"})

    assert response.status_code == 422


def test_custom_selected_model_can_be_saved_outside_catalog(client):
    response = client.patch(
        "/api/v1/llm/settings",
        json={
            "llm_provider": "openai",
            "enable_llm_reasoning": True,
            "selected_model": "gpt-future-model-test",
            "api_key": "sk-test-secret-abcd",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["selected_model"] == "gpt-future-model-test"
    assert body["masked_api_key"] == "sk-****abcd"
    assert "sk-test-secret-abcd" not in str(body)
