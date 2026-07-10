from app.llm.base import StubbedLLMProvider


class AnthropicLLMProvider(StubbedLLMProvider):
    def __init__(self, api_key: str | None, model_name: str = "claude-3-5-haiku-latest") -> None:
        super().__init__(provider_name="anthropic", model_name=model_name, api_key=api_key)
