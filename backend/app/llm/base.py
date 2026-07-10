from app.llm.prompts import get_prompt
from app.llm.schemas import LLMDecisionContext, LLMGenerationResponse, LLMStatusResponse


class BaseLLMProvider:
    provider_name = "disabled"
    model_name = "none"
    enabled = False
    available = False

    def __init__(self, warnings: list[str] | None = None, model_name: str | None = None) -> None:
        if model_name is not None:
            self.model_name = model_name
        self.warnings = warnings or []

    def status(self) -> LLMStatusResponse:
        return LLMStatusResponse(
            llm_provider=self.provider_name,
            enabled=self.enabled,
            available=self.available,
            model=self.model_name,
            warnings=self.warnings,
        )

    def generate_bull_bear_summary(self, context: LLMDecisionContext) -> LLMGenerationResponse:
        return self._not_used_response("bull_bear_summary")

    def generate_decision_memo(self, context: LLMDecisionContext) -> LLMGenerationResponse:
        return self._not_used_response("decision_memo")

    def generate_risk_explanation(self, context: LLMDecisionContext) -> LLMGenerationResponse:
        return self._not_used_response("risk_explanation")

    def generate_research_report(self, context: LLMDecisionContext) -> LLMGenerationResponse:
        return self._not_used_response("research_report")

    def _not_used_response(self, prompt_key: str) -> LLMGenerationResponse:
        prompt = get_prompt(prompt_key)
        warnings = self.warnings or ["LLM reasoning disabled."]
        return LLMGenerationResponse(
            provider=self.provider_name,
            model=self.model_name,
            enabled=self.enabled,
            used=False,
            summary="",
            reasoning_notes=[],
            warnings=warnings,
            prompt_name=prompt.prompt_name,
            prompt_version=prompt.prompt_version,
        )


class DisabledLLMProvider(BaseLLMProvider):
    model_name = "none"
    enabled = False
    available = False

    def __init__(
        self,
        provider_name: str = "disabled",
        warnings: list[str] | None = None,
        model_name: str | None = None,
    ) -> None:
        self.provider_name = provider_name
        super().__init__(warnings=warnings or ["LLM reasoning disabled."], model_name=model_name)


class StubbedLLMProvider(DisabledLLMProvider):
    def __init__(
        self,
        provider_name: str,
        model_name: str,
        api_key: str | None,
        requires_api_key: bool = True,
    ) -> None:
        if requires_api_key and not api_key:
            warning = "API key is missing for selected provider; falling back to deterministic mode."
        else:
            warning = "Provider configuration is available, but live API calls are not implemented in this phase."
        super().__init__(
            provider_name=provider_name,
            warnings=[warning],
            model_name=model_name,
        )
