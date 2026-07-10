from app.llm.anthropic_provider import AnthropicLLMProvider
from app.llm.base import BaseLLMProvider, DisabledLLMProvider, StubbedLLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_provider import OpenAILLMProvider
from app.llm.schemas import LLMStatusResponse
from app.llm.settings_store import PROVIDERS_REQUIRING_KEYS, read_llm_settings_raw


def get_llm_provider() -> BaseLLMProvider:
    settings = read_llm_settings_raw()
    configured_provider = settings["llm_provider"]
    enabled = settings["enable_llm_reasoning"]
    model_name = settings["selected_model"]
    api_key = settings.get("api_key", "")

    if not enabled:
        return DisabledLLMProvider(
            provider_name=configured_provider,
            model_name=model_name,
            warnings=["LLM reasoning disabled by saved settings or environment fallback."],
        )

    if configured_provider == "disabled":
        return DisabledLLMProvider(
            provider_name="disabled",
            model_name=model_name,
            warnings=["LLM_PROVIDER=disabled; deterministic mode used."],
        )
    if configured_provider == "mock":
        return MockLLMProvider(model_name=model_name)
    if configured_provider == "openai":
        return OpenAILLMProvider(api_key=api_key, model_name=model_name)
    if configured_provider == "anthropic":
        return AnthropicLLMProvider(api_key=api_key, model_name=model_name)
    if configured_provider in {
        "gemini",
        "deepseek",
        "xai",
        "mistral",
        "groq",
        "openrouter",
        "ollama",
        "custom_openai_compatible",
    }:
        return StubbedLLMProvider(
            provider_name=configured_provider,
            model_name=model_name,
            api_key=api_key,
            requires_api_key=configured_provider in PROVIDERS_REQUIRING_KEYS,
        )

    return DisabledLLMProvider(
        provider_name=configured_provider,
        model_name=model_name,
        warnings=[f"Unknown LLM_PROVIDER '{configured_provider}'; deterministic mode used."],
    )


def get_llm_status() -> LLMStatusResponse:
    return get_llm_provider().status()
