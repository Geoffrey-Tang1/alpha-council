import json
import os
import time
from pathlib import Path
from typing import Any

from app.llm.schemas import (
    LLMConnectionTestRequest,
    LLMConnectionTestResponse,
    LLMProviderName,
    LLMSettingsResponse,
    LLMSettingsUpdate,
    utc_now_iso,
)


MODEL_OPTIONS: dict[str, list[str]] = {
    "disabled": [],
    "mock": ["mock-llm-v1"],
    "openai": [
        "gpt-5.5",
        "gpt-5.5-pro",
        "gpt-5.4",
        "gpt-5.4-pro",
        "gpt-5.4-mini",
        "gpt-5.4-nano",
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4o",
        "gpt-4o-mini",
    ],
    "anthropic": [
        "claude-opus-4-1",
        "claude-sonnet-4",
        "claude-3-7-sonnet-latest",
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
    ],
    "gemini": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "xai": ["grok-4", "grok-3", "grok-3-mini", "grok-2", "grok-2-mini"],
    "mistral": ["mistral-large-latest", "mistral-small-latest", "magistral-medium-latest", "magistral-small-latest"],
    "groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "moonshotai/kimi-k2-instruct",
        "qwen/qwen3-32b",
        "deepseek-r1-distill-llama-70b",
    ],
    "openrouter": ["openrouter/auto"],
    "ollama": ["llama3.1", "llama3.2", "qwen2.5", "qwen3", "mistral", "deepseek-r1"],
    "custom_openai_compatible": [],
}

PROVIDERS_REQUIRING_KEYS = {
    "openai",
    "anthropic",
    "gemini",
    "deepseek",
    "xai",
    "mistral",
    "groq",
    "openrouter",
    "custom_openai_compatible",
}

DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "xai": "https://api.x.ai/v1",
    "mistral": "https://api.mistral.ai/v1",
    "groq": "https://api.groq.com/openai/v1",
    "ollama": "http://localhost:11434",
}

ENV_KEY_NAMES = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "xai": "XAI_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "custom_openai_compatible": "CUSTOM_OPENAI_API_KEY",
}

DEFAULT_SETTINGS = {
    "llm_provider": "disabled",
    "enable_llm_reasoning": False,
    "selected_model": "none",
    "api_key": "",
    "base_url": None,
    "temperature": 0.2,
    "max_tokens": 1200,
    "timeout_seconds": 30,
    "last_connection_status": "not_tested",
    "last_connection_message": "Connection has not been tested.",
    "updated_at": None,
}


def settings_file_path() -> Path:
    configured_path = os.getenv("LLM_SETTINGS_PATH")
    if configured_path:
        return Path(configured_path)
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root / "local_settings" / "llm_settings.json"


def available_models_for(provider: str) -> list[str]:
    return MODEL_OPTIONS.get(provider, ["custom-model"])


def default_model_for(provider: str) -> str:
    models = available_models_for(provider)
    if models:
        return models[0]
    return "none" if provider == "disabled" else "custom-model"


def mask_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    key = api_key.strip()
    if not key:
        return None
    suffix = key[-4:]
    if "-" in key[:12]:
        prefix = key.split("-", 1)[0] + "-"
    else:
        prefix = key[:3] if len(key) > 7 else ""
    return f"{prefix}****{suffix}"


def read_llm_settings_raw() -> dict[str, Any]:
    path = settings_file_path()
    if path.exists():
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            payload = {}
        return _normalize_settings({**DEFAULT_SETTINGS, **payload})
    return _normalize_settings(_environment_fallback_settings())


def get_llm_settings_response() -> LLMSettingsResponse:
    return _to_response(read_llm_settings_raw())


def update_llm_settings(update: LLMSettingsUpdate) -> LLMSettingsResponse:
    current = read_llm_settings_raw()
    previous_provider = str(current.get("llm_provider", "disabled"))
    fields = update.model_fields_set
    update_payload = update.model_dump(exclude_unset=True)

    for field, value in update_payload.items():
        if field == "api_key":
            continue
        current[field] = value

    provider = str(current.get("llm_provider", "disabled"))
    if "selected_model" not in fields:
        current["selected_model"] = default_model_for(provider)
    if "base_url" not in fields and provider in DEFAULT_BASE_URLS:
        current["base_url"] = DEFAULT_BASE_URLS[provider]
    if "llm_provider" in fields and provider != previous_provider:
        current["last_connection_status"] = "not_tested"
        current["last_connection_message"] = "Connection has not been tested."

    if "api_key" in fields:
        if update.api_key == "":
            current["api_key"] = ""
        elif update.api_key is not None:
            current["api_key"] = update.api_key

    current["updated_at"] = utc_now_iso()
    saved = _normalize_settings(current)
    _write_settings(saved)
    return _to_response(saved)


def test_llm_connection(request: LLMConnectionTestRequest) -> LLMConnectionTestResponse:
    start = time.monotonic()
    current = read_llm_settings_raw()
    provider = str(request.llm_provider)
    model = request.selected_model or current.get("selected_model") or default_model_for(provider)
    api_key = request.api_key if request.api_key not in {None, ""} else current.get("api_key", "")

    if provider == "mock":
        success = True
        message = "Mock LLM provider is available."
    elif provider == "disabled":
        success = False
        message = "LLM provider is disabled."
    elif provider in PROVIDERS_REQUIRING_KEYS and not api_key:
        success = False
        message = "API key is missing for selected provider; falling back to deterministic mode."
    else:
        success = False
        message = "Provider configuration is available, but live API calls are not implemented in this phase."

    latency_ms = max(1, int((time.monotonic() - start) * 1000))
    current["llm_provider"] = provider
    current["selected_model"] = model
    current["base_url"] = request.base_url if request.base_url is not None else current.get("base_url")
    current["last_connection_status"] = "success" if success else "failed"
    current["last_connection_message"] = message
    current["updated_at"] = utc_now_iso()
    _write_settings(_normalize_settings(current))

    return LLMConnectionTestResponse(
        success=success,
        provider=LLMProviderName(provider),
        model=model,
        message=message,
        latency_ms=latency_ms,
    )


def _environment_fallback_settings() -> dict[str, Any]:
    provider = os.getenv("LLM_PROVIDER", "disabled").strip().lower() or "disabled"
    enabled = os.getenv("ENABLE_LLM_REASONING", "false").strip().lower() == "true"
    api_key = os.getenv(ENV_KEY_NAMES.get(provider, ""), "")
    return {
        **DEFAULT_SETTINGS,
        "llm_provider": provider,
        "enable_llm_reasoning": enabled,
        "selected_model": os.getenv("LLM_MODEL", default_model_for(provider)),
        "api_key": api_key,
        "base_url": os.getenv("LLM_BASE_URL") or DEFAULT_BASE_URLS.get(provider),
        "updated_at": utc_now_iso(),
    }


def _normalize_settings(settings: dict[str, Any]) -> dict[str, Any]:
    provider = str(settings.get("llm_provider", "disabled")).strip().lower() or "disabled"
    if provider not in MODEL_OPTIONS:
        provider = "disabled"
    settings["llm_provider"] = provider
    settings["enable_llm_reasoning"] = bool(settings.get("enable_llm_reasoning", False))
    settings["selected_model"] = settings.get("selected_model") or default_model_for(provider)
    settings["api_key"] = settings.get("api_key") or ""
    settings["base_url"] = settings.get("base_url") or DEFAULT_BASE_URLS.get(provider)
    settings["temperature"] = float(settings.get("temperature", DEFAULT_SETTINGS["temperature"]))
    settings["max_tokens"] = int(settings.get("max_tokens", DEFAULT_SETTINGS["max_tokens"]))
    settings["timeout_seconds"] = int(settings.get("timeout_seconds", DEFAULT_SETTINGS["timeout_seconds"]))
    settings["last_connection_status"] = settings.get("last_connection_status") or "not_tested"
    settings["last_connection_message"] = settings.get("last_connection_message") or "Connection has not been tested."
    settings["updated_at"] = settings.get("updated_at") or utc_now_iso()
    return settings


def _to_response(settings: dict[str, Any]) -> LLMSettingsResponse:
    api_key = settings.get("api_key", "")
    return LLMSettingsResponse(
        llm_provider=LLMProviderName(settings["llm_provider"]),
        enable_llm_reasoning=settings["enable_llm_reasoning"],
        selected_model=settings["selected_model"],
        api_key_present=bool(api_key),
        masked_api_key=mask_api_key(api_key),
        base_url=settings.get("base_url"),
        temperature=settings["temperature"],
        max_tokens=settings["max_tokens"],
        timeout_seconds=settings["timeout_seconds"],
        available_models=available_models_for(settings["llm_provider"]),
        last_connection_status=settings["last_connection_status"],
        last_connection_message=settings["last_connection_message"],
        updated_at=settings["updated_at"],
    )


def _write_settings(settings: dict[str, Any]) -> None:
    path = settings_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, sort_keys=True))
