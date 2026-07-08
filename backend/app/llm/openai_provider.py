from app.llm.base import DisabledLLMProvider


class OpenAILLMProvider(DisabledLLMProvider):
    def __init__(self, api_key: str | None) -> None:
        if not api_key:
            warning = "LLM_PROVIDER=openai selected but OPENAI_API_KEY is missing; deterministic mode used."
        else:
            warning = "OpenAI provider is a safe Phase 6 stub; external calls are not enabled in this MVP."
        super().__init__(provider_name="openai", warnings=[warning])
