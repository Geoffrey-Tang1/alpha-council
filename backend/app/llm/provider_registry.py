import os

from app.llm.anthropic_provider import AnthropicLLMProvider
from app.llm.base import BaseLLMProvider, DisabledLLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_provider import OpenAILLMProvider
from app.llm.schemas import LLMStatusResponse


def get_llm_provider() -> BaseLLMProvider:
    configured_provider = os.getenv("LLM_PROVIDER", "disabled").strip().lower() or "disabled"
    enabled = os.getenv("ENABLE_LLM_REASONING", "false").strip().lower() == "true"

    if not enabled:
        return DisabledLLMProvider(
            provider_name=configured_provider,
            warnings=["LLM reasoning disabled by ENABLE_LLM_REASONING=false."],
        )

    if configured_provider == "disabled":
        return DisabledLLMProvider(
            provider_name="disabled",
            warnings=["LLM_PROVIDER=disabled; deterministic mode used."],
        )
    if configured_provider == "mock":
        return MockLLMProvider()
    if configured_provider == "openai":
        return OpenAILLMProvider(api_key=os.getenv("OPENAI_API_KEY", ""))
    if configured_provider == "anthropic":
        return AnthropicLLMProvider(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

    return DisabledLLMProvider(
        provider_name=configured_provider,
        warnings=[f"Unknown LLM_PROVIDER '{configured_provider}'; deterministic mode used."],
    )


def get_llm_status() -> LLMStatusResponse:
    return get_llm_provider().status()
