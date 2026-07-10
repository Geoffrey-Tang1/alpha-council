from app.llm.base import BaseLLMProvider
from app.llm.prompts import get_prompt
from app.llm.schemas import LLMDecisionContext, LLMGenerationResponse


class MockLLMProvider(BaseLLMProvider):
    provider_name = "mock"
    model_name = "mock-llm-v1"
    enabled = True
    available = True

    def __init__(self, model_name: str = "mock-llm-v1") -> None:
        super().__init__(
            warnings=["Mock LLM provider active; outputs are deterministic development summaries."],
            model_name=model_name,
        )

    def generate_bull_bear_summary(self, context: LLMDecisionContext) -> LLMGenerationResponse:
        bull = "; ".join(context.bull_points[:2]) or "No strong bull evidence."
        bear = "; ".join(context.bear_points[:2]) or "No strong bear evidence."
        summary = (
            f"This mock LLM bull/bear summary uses deterministic AlphaCouncil evidence for "
            f"{self._instrument(context)}. Bull case: {bull} Bear case: {bear}"
            f"{self._data_limitation(context)}"
        )
        return self._used_response("bull_bear_summary", summary)

    def generate_decision_memo(self, context: LLMDecisionContext) -> LLMGenerationResponse:
        veto_note = (
            f" Risk Manager veto is active: {context.risk_veto_reason}."
            if context.risk_veto
            else " Risk controls did not add a veto."
        )
        summary = (
            f"This mock LLM memo summarizes the deterministic AlphaCouncil decision for "
            f"{self._instrument(context)}: {context.decision} with {context.confidence:.0%} confidence. "
            f"{context.final_explanation}{veto_note} It is research support only and not a guarantee."
            f"{self._data_limitation(context)}"
        )
        return self._used_response("decision_memo", summary)

    def generate_risk_explanation(self, context: LLMDecisionContext) -> LLMGenerationResponse:
        warnings = "; ".join(context.risk_warnings[:3]) or "No additional deterministic warnings."
        summary = (
            f"Risk explanation for {self._instrument(context)}: max position size remains "
            f"{context.max_position_size_pct:.2f}% and stop-loss discipline is required. "
            f"Key warnings: {warnings} The LLM does not set vetoes, sizing, stops, or targets."
            f"{self._data_limitation(context)}"
        )
        return self._used_response("risk_explanation", summary)

    def generate_research_report(self, context: LLMDecisionContext) -> LLMGenerationResponse:
        summary = (
            f"Mock LLM research report for {self._instrument(context)}. Technical view: "
            f"{context.technical_view} Fundamental view: {context.fundamental_view} "
            f"News/sentiment view: {context.news_view} Macro view: {context.macro_view} "
            f"Final deterministic decision: {context.decision}. Invalidation conditions: "
            f"{'; '.join(context.invalidation_conditions) or 'None listed.'} This report is explanatory only."
            f"{self._data_limitation(context)}"
        )
        return self._used_response("research_report", summary)

    def _used_response(self, prompt_key: str, summary: str) -> LLMGenerationResponse:
        prompt = get_prompt(prompt_key)
        return LLMGenerationResponse(
            provider=self.provider_name,
            model=self.model_name,
            enabled=True,
            used=True,
            summary=summary,
            reasoning_notes=[
                "Generated from deterministic AlphaCouncil outputs only.",
                "No chain-of-thought, executable orders, or guaranteed-return claims are produced.",
            ],
            warnings=list(self.warnings),
            prompt_name=prompt.prompt_name,
            prompt_version=prompt.prompt_version,
        )

    def _instrument(self, context: LLMDecisionContext) -> str:
        return f"{context.company_name} ({context.display_symbol or context.ticker})"

    def _data_limitation(self, context: LLMDecisionContext) -> str:
        if context.data_quality == "REAL":
            return " Market data may still be delayed or incomplete; this is not financial advice."
        return f" Data quality is {context.data_quality}, so the memo treats evidence as limited."
