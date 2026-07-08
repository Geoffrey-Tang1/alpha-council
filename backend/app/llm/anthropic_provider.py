from app.llm.base import DisabledLLMProvider


class AnthropicLLMProvider(DisabledLLMProvider):
    def __init__(self, api_key: str | None) -> None:
        if not api_key:
            warning = "LLM_PROVIDER=anthropic selected but ANTHROPIC_API_KEY is missing; deterministic mode used."
        else:
            warning = "Anthropic provider is a safe Phase 6 stub; external calls are not enabled in this MVP."
        super().__init__(provider_name="anthropic", warnings=[warning])
