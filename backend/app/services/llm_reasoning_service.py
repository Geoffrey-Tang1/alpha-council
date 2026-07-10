from app.llm.provider_registry import get_llm_provider
from app.llm.prompts import get_prompt
from app.llm.schemas import LLMDecisionContext, LLMDecisionOutputs, LLMGenerationResponse
from app.schemas.decisions import DecisionResponse


class LLMReasoningService:
    def enrich_decision(self, decision: DecisionResponse) -> DecisionResponse:
        provider = get_llm_provider()
        decision.llm_provider = provider.provider_name
        decision.llm_model = provider.model_name
        decision.llm_enabled = provider.enabled

        if not provider.enabled:
            decision.llm_used = False
            decision.llm_warnings = list(dict.fromkeys(provider.warnings or ["LLM reasoning disabled."]))
            decision.llm_outputs = LLMDecisionOutputs()
            return decision

        context = self._build_context(decision)
        outputs = LLMDecisionOutputs(
            bull_bear_summary=self._safe_generate(provider.generate_bull_bear_summary, context, "bull_bear_summary"),
            risk_explanation=self._safe_generate(provider.generate_risk_explanation, context, "risk_explanation"),
            decision_memo=self._safe_generate(provider.generate_decision_memo, context, "decision_memo"),
            research_report=self._safe_generate(provider.generate_research_report, context, "research_report"),
        )
        responses = [
            outputs.bull_bear_summary,
            outputs.risk_explanation,
            outputs.decision_memo,
            outputs.research_report,
        ]
        outputs.prompt_versions = {
            response.prompt_name: response.prompt_version
            for response in responses
            if response is not None
        }
        decision.llm_outputs = outputs
        decision.llm_used = any(response.used for response in responses if response is not None)
        warnings: list[str] = [*provider.warnings]
        for response in responses:
            if response is not None:
                warnings.extend(response.warnings)
        decision.llm_warnings = list(dict.fromkeys(warnings))
        return decision

    def _safe_generate(self, generator, context: LLMDecisionContext, prompt_key: str) -> LLMGenerationResponse:
        try:
            return generator(context)
        except Exception as exc:  # pragma: no cover - defensive guard for future real providers
            prompt = get_prompt(prompt_key)
            return LLMGenerationResponse(
                provider="error",
                model="none",
                enabled=False,
                used=False,
                summary="",
                reasoning_notes=[],
                warnings=[f"LLM generation failed for {prompt.prompt_name}: {exc}"],
                prompt_name=prompt.prompt_name,
                prompt_version=prompt.prompt_version,
            )

    def _build_context(self, decision: DecisionResponse) -> LLMDecisionContext:
        outputs = decision.agent_outputs
        risk = outputs.risk_manager
        return LLMDecisionContext(
            ticker=decision.ticker,
            company_name=decision.company_name,
            display_symbol=decision.display_symbol or decision.normalized_ticker or decision.ticker,
            market=str(decision.market),
            decision=str(decision.decision),
            confidence=decision.confidence,
            data_provider=decision.data_provider,
            data_quality=decision.data_quality,
            data_warnings=decision.data_warnings,
            risk_warnings=decision.risk_warnings,
            invalidation_conditions=decision.invalidation_conditions,
            final_explanation=decision.final_explanation,
            entry_plan=decision.entry_plan,
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit,
            max_position_size_pct=decision.max_position_size_pct,
            risk_veto=risk.veto,
            risk_veto_reason=risk.veto_reason,
            technical_view=outputs.technical_analysis.explanation,
            fundamental_view=outputs.fundamental_analysis.explanation,
            news_view=outputs.news_sentiment.explanation,
            macro_view=outputs.macro_cross_market.explanation,
            bull_points=decision.bull_case.bull_points,
            bear_points=decision.bear_case.bear_points,
            portfolio_fit=outputs.portfolio_manager.portfolio_fit,
        )
