from app.llm.base import StubbedLLMProvider


class OpenAILLMProvider(StubbedLLMProvider):
    def __init__(self, api_key: str | None, model_name: str = "gpt-4.1-mini") -> None:
        super().__init__(provider_name="openai", model_name=model_name, api_key=api_key)
