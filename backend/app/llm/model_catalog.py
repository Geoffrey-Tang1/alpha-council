import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.llm.schemas import LLMModelCatalogResponse, LLMModelInfo, LLMProviderName, utc_now_iso
from app.llm.settings_store import (
    DEFAULT_BASE_URLS,
    ENV_KEY_NAMES,
    MODEL_OPTIONS,
    PROVIDERS_REQUIRING_KEYS,
    read_llm_settings_raw,
)


OPENAI_COMPATIBLE_PROVIDERS = {
    "openai",
    "openrouter",
    "custom_openai_compatible",
    "deepseek",
    "xai",
    "mistral",
    "groq",
}
REFRESH_SUPPORTED_PROVIDERS = OPENAI_COMPATIBLE_PROVIDERS | {"anthropic", "ollama"}


def model_catalog_cache_path() -> Path:
    configured_path = os.getenv("LLM_MODEL_CACHE_PATH")
    if configured_path:
        return Path(configured_path)
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root / "local_settings" / "model_catalog_cache.json"


def get_provider_model_catalog(provider: LLMProviderName) -> LLMModelCatalogResponse:
    provider_name = str(provider)
    if provider_name in {"disabled", "mock"}:
        return _static_response(provider_name)

    cached = _read_cached_provider(provider_name)
    if cached:
        models = [_model_from_payload(model, source="cache") for model in cached.get("models", [])]
        return LLMModelCatalogResponse(
            provider=LLMProviderName(provider_name),
            models=models,
            source="cache",
            fetched_at=cached.get("fetched_at"),
            status=cached.get("status") or "success",
            message="Loaded from local cache.",
            supports_refresh=_supports_refresh(provider_name),
        )

    return _static_response(provider_name)


def refresh_provider_model_catalog(provider: LLMProviderName) -> LLMModelCatalogResponse:
    provider_name = str(provider)
    if provider_name in {"disabled", "mock"}:
        return _static_response(provider_name)
    if not _supports_refresh(provider_name):
        return _static_response(
            provider_name,
            status="unsupported",
            message="Live model refresh is not implemented for this provider yet. Showing fallback models.",
        )

    settings = read_llm_settings_raw()
    api_key = _api_key_for_provider(provider_name, settings)
    base_url = _base_url_for_provider(provider_name, settings)
    timeout_seconds = int(settings.get("timeout_seconds", 30))

    if provider_name in PROVIDERS_REQUIRING_KEYS and not api_key:
        return _static_response(
            provider_name,
            status="missing_api_key",
            message=f"API key is required to refresh {provider_name_label(provider_name)} models. Showing fallback models.",
        )
    if provider_name == "custom_openai_compatible" and not base_url:
        return _static_response(
            provider_name,
            status="missing_base_url",
            message="Base URL is required to refresh custom OpenAI-compatible models. Showing fallback models.",
        )

    try:
        live_models = _fetch_live_models(provider_name, api_key=api_key, base_url=base_url, timeout_seconds=timeout_seconds)
    except Exception:
        return _static_response(
            provider_name,
            status="error",
            message=f"Could not refresh {provider_name_label(provider_name)} models. Showing fallback models.",
        )

    if not live_models:
        return _static_response(
            provider_name,
            status="unavailable",
            message=f"No models were returned by {provider_name_label(provider_name)}. Showing fallback models.",
        )

    fetched_at = utc_now_iso()
    models = [_model_from_payload(model, source="live") for model in live_models]
    message = f"Loaded {len(models)} models from {provider_name_label(provider_name)}."
    _write_cached_provider(
        provider_name,
        {
            "models": [model.model_dump() for model in models],
            "fetched_at": fetched_at,
            "status": "success",
            "message": message,
        },
    )
    return LLMModelCatalogResponse(
        provider=LLMProviderName(provider_name),
        models=models,
        source="live",
        fetched_at=fetched_at,
        status="success",
        message=message,
        supports_refresh=True,
    )


def provider_name_label(provider: str) -> str:
    labels = {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "gemini": "Gemini",
        "deepseek": "DeepSeek",
        "xai": "xAI",
        "mistral": "Mistral",
        "groq": "Groq",
        "openrouter": "OpenRouter",
        "ollama": "Ollama",
        "custom_openai_compatible": "custom OpenAI-compatible",
    }
    return labels.get(provider, provider)


def _static_response(provider: str, status: str | None = None, message: str | None = None) -> LLMModelCatalogResponse:
    if provider == "disabled":
        status = status or "disabled"
        message = message or "LLM provider is disabled."
    elif provider == "mock":
        status = status or "static"
        message = message or "Mock model list is static."
    else:
        status = status or "static"
        message = message or f"Showing static fallback models for {provider_name_label(provider)}."

    return LLMModelCatalogResponse(
        provider=LLMProviderName(provider),
        models=_static_models(provider),
        source="static",
        fetched_at=None,
        status=status,
        message=message,
        supports_refresh=_supports_refresh(provider),
    )


def _static_models(provider: str) -> list[LLMModelInfo]:
    return [
        LLMModelInfo(id=model_id, name=model_id, source="static", metadata={})
        for model_id in MODEL_OPTIONS.get(provider, [])
    ]


def _supports_refresh(provider: str) -> bool:
    return provider in REFRESH_SUPPORTED_PROVIDERS


def _api_key_for_provider(provider: str, settings: dict[str, Any]) -> str:
    if settings.get("llm_provider") == provider:
        return settings.get("api_key", "")
    env_key = ENV_KEY_NAMES.get(provider)
    return os.getenv(env_key, "") if env_key else ""


def _base_url_for_provider(provider: str, settings: dict[str, Any]) -> str | None:
    if settings.get("llm_provider") == provider and settings.get("base_url"):
        return str(settings["base_url"])
    return os.getenv("LLM_BASE_URL") or DEFAULT_BASE_URLS.get(provider)


def _fetch_live_models(provider: str, api_key: str, base_url: str | None, timeout_seconds: int) -> list[dict[str, Any]]:
    if provider == "anthropic":
        return _fetch_anthropic_models(api_key=api_key, timeout_seconds=timeout_seconds)
    if provider == "ollama":
        return _fetch_ollama_models(base_url=base_url or DEFAULT_BASE_URLS["ollama"], timeout_seconds=timeout_seconds)
    if provider in OPENAI_COMPATIBLE_PROVIDERS:
        return _fetch_openai_compatible_models(
            base_url=base_url or DEFAULT_BASE_URLS.get(provider),
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
    raise ValueError("Provider does not support live model refresh.")


def _fetch_openai_compatible_models(base_url: str | None, api_key: str, timeout_seconds: int) -> list[dict[str, Any]]:
    if not base_url:
        raise ValueError("Base URL is required.")
    endpoint = base_url.rstrip("/") + "/models"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = _get_json(endpoint, headers=headers, timeout_seconds=timeout_seconds)
    raw_models = payload.get("data", payload if isinstance(payload, list) else [])
    return [
        {
            "id": str(model.get("id") or model.get("name")),
            "name": str(model.get("id") or model.get("name")),
            "created": model.get("created"),
            "metadata": _safe_metadata(model),
        }
        for model in raw_models
        if isinstance(model, dict) and (model.get("id") or model.get("name"))
    ]


def _fetch_anthropic_models(api_key: str, timeout_seconds: int) -> list[dict[str, Any]]:
    payload = _get_json(
        "https://api.anthropic.com/v1/models",
        headers={
            "Accept": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        timeout_seconds=timeout_seconds,
    )
    raw_models = payload.get("data", [])
    return [
        {
            "id": str(model.get("id")),
            "name": str(model.get("display_name") or model.get("id")),
            "created": model.get("created_at"),
            "metadata": _safe_metadata(model),
        }
        for model in raw_models
        if isinstance(model, dict) and model.get("id")
    ]


def _fetch_ollama_models(base_url: str, timeout_seconds: int) -> list[dict[str, Any]]:
    payload = _get_json(
        base_url.rstrip("/") + "/api/tags",
        headers={"Accept": "application/json"},
        timeout_seconds=timeout_seconds,
    )
    raw_models = payload.get("models", [])
    return [
        {
            "id": str(model.get("name") or model.get("model")),
            "name": str(model.get("name") or model.get("model")),
            "created": model.get("modified_at"),
            "metadata": _safe_metadata(model),
        }
        for model in raw_models
        if isinstance(model, dict) and (model.get("name") or model.get("model"))
    ]


def _get_json(url: str, headers: dict[str, str], timeout_seconds: int) -> dict[str, Any] | list[Any]:
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(_sanitize_error(exc)) from exc


def _sanitize_error(exc: Exception) -> str:
    return f"{exc.__class__.__name__}: model list request failed."


def _safe_metadata(model: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in model.items()
        if key not in {"id", "name", "display_name", "created", "created_at", "modified_at"}
        and key.lower() not in {"authorization", "api_key", "x-api-key"}
    }


def _model_from_payload(payload: dict[str, Any] | LLMModelInfo, source: str) -> LLMModelInfo:
    if isinstance(payload, LLMModelInfo):
        return payload.model_copy(update={"source": source})
    model_id = str(payload.get("id") or payload.get("name"))
    return LLMModelInfo(
        id=model_id,
        name=str(payload.get("name") or model_id),
        source=source,
        created=payload.get("created"),
        metadata=payload.get("metadata") or {},
    )


def _read_cache() -> dict[str, Any]:
    path = model_catalog_cache_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def _read_cached_provider(provider: str) -> dict[str, Any] | None:
    cached = _read_cache()
    provider_payload = cached.get(provider)
    return provider_payload if isinstance(provider_payload, dict) else None


def _write_cached_provider(provider: str, payload: dict[str, Any]) -> None:
    path = model_catalog_cache_path()
    cache = _read_cache()
    cache[provider] = payload
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, sort_keys=True))
