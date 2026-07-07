from datetime import datetime, timezone
from uuid import uuid4

from app.agents.base import BaseAgent
from app.core.constants import AgentSignal, DecisionAction
from app.schemas.agents import (
    AgentVoteOutput,
    BearCaseOutput,
    BullCaseOutput,
    FundamentalAnalysisOutput,
    MacroAnalysisOutput,
    NewsSentimentOutput,
    PortfolioManagerOutput,
    RiskManagerOutput,
    TechnicalAnalysisOutput,
)
from app.schemas.common import DataSource
from app.schemas.decisions import DecisionResponse


class DecisionCommitteeAgent(BaseAgent):
    name = "decision_committee"

    def decide(
        self,
        collected_data: dict,
        time_horizon: str,
        technical: TechnicalAnalysisOutput,
        fundamental: FundamentalAnalysisOutput,
        news: NewsSentimentOutput,
        macro: MacroAnalysisOutput,
        bull_case: BullCaseOutput,
        bear_case: BearCaseOutput,
        risk: RiskManagerOutput,
        portfolio: PortfolioManagerOutput,
    ) -> DecisionResponse:
        latest_price = collected_data.get("latest_price")
        stop_loss = round(latest_price * 0.95, 2) if latest_price else None
        take_profit = round(latest_price * 1.1, 2) if latest_price else None

        base_decision = self._base_decision(technical, fundamental, news, macro)
        if risk.veto and base_decision == DecisionAction.BUY:
            final_decision = DecisionAction.WATCH
        elif risk.veto:
            final_decision = DecisionAction.AVOID
        elif collected_data.get("data_source_status", {}).get("is_mock"):
            final_decision = DecisionAction.WATCH
        else:
            final_decision = base_decision

        if final_decision == DecisionAction.BUY and stop_loss is None:
            final_decision = DecisionAction.WATCH

        confidence = self._confidence(technical, fundamental, news, macro, risk)
        market_status = collected_data["market_status"].status

        agent_votes = [
            AgentVoteOutput(agent="technical_analysis", vote=self._signal_to_decision(technical.technical_signal), confidence=technical.confidence),
            AgentVoteOutput(agent="fundamental_analysis", vote=self._signal_to_decision(fundamental.fundamental_signal), confidence=fundamental.confidence),
            AgentVoteOutput(agent="news_sentiment", vote=self._signal_to_decision(news.sentiment_signal), confidence=news.confidence),
            AgentVoteOutput(agent="macro_cross_market", vote=self._signal_to_decision(macro.macro_signal), confidence=macro.confidence),
            AgentVoteOutput(
                agent="risk_manager",
                vote=DecisionAction.AVOID if risk.veto else DecisionAction.WATCH,
                confidence=max(0.55, min(0.9, 0.7 - abs(risk.confidence_adjustment))),
            ),
        ]

        risk_warnings = list(risk.risk_warnings)
        if risk.veto_reason:
            risk_warnings.append(f"Risk veto: {risk.veto_reason}")
        if portfolio.concentration_warning:
            risk_warnings.append(portfolio.concentration_warning)

        return DecisionResponse(
            decision_id=f"dec_{uuid4().hex}",
            ticker=collected_data["ticker"],
            market=collected_data["market"],
            latest_price=latest_price,
            market_status=market_status,
            decision=final_decision,
            confidence=confidence,
            time_horizon=time_horizon,
            entry_plan=self._entry_plan(final_decision),
            stop_loss=stop_loss,
            take_profit=take_profit,
            max_position_size_pct=portfolio.recommended_position_size_pct,
            bull_case=bull_case,
            bear_case=bear_case,
            risk_warnings=risk_warnings,
            invalidation_conditions=self._invalidation_conditions(stop_loss),
            agent_votes=agent_votes,
            final_explanation=self._final_explanation(final_decision, risk),
            data_sources=[
                DataSource(
                    name=collected_data["data_source_status"]["provider_name"],
                    type="market_data",
                    status=collected_data["data_source_status"]["status"],
                )
            ],
            timestamp=datetime.now(timezone.utc).isoformat(),
            saved=False,
        )

    def _base_decision(
        self,
        technical: TechnicalAnalysisOutput,
        fundamental: FundamentalAnalysisOutput,
        news: NewsSentimentOutput,
        macro: MacroAnalysisOutput,
    ) -> DecisionAction:
        positive = sum(
            signal == AgentSignal.BUY
            for signal in [
                technical.technical_signal,
                fundamental.fundamental_signal,
                news.sentiment_signal,
                macro.macro_signal,
            ]
        )
        negative = sum(
            signal in {AgentSignal.SELL, AgentSignal.AVOID}
            for signal in [
                technical.technical_signal,
                fundamental.fundamental_signal,
                news.sentiment_signal,
                macro.macro_signal,
            ]
        )
        if negative >= 2:
            return DecisionAction.AVOID
        if positive >= 2:
            return DecisionAction.BUY
        if technical.technical_signal == AgentSignal.BUY:
            return DecisionAction.WATCH
        return DecisionAction.HOLD

    def _confidence(
        self,
        technical: TechnicalAnalysisOutput,
        fundamental: FundamentalAnalysisOutput,
        news: NewsSentimentOutput,
        macro: MacroAnalysisOutput,
        risk: RiskManagerOutput,
    ) -> float:
        average = (technical.confidence + fundamental.confidence + news.confidence + macro.confidence) / 4
        adjusted = average + risk.confidence_adjustment
        return round(max(0.0, min(1.0, adjusted)), 2)

    def _signal_to_decision(self, signal: AgentSignal) -> DecisionAction:
        mapping = {
            AgentSignal.BUY: DecisionAction.BUY,
            AgentSignal.SELL: DecisionAction.SELL,
            AgentSignal.HOLD: DecisionAction.HOLD,
            AgentSignal.WATCH: DecisionAction.WATCH,
            AgentSignal.AVOID: DecisionAction.AVOID,
        }
        return mapping[signal]

    def _entry_plan(self, decision: DecisionAction) -> str:
        if decision == DecisionAction.BUY:
            return "Consider entry only after confirming liquidity and respecting the stop loss."
        if decision == DecisionAction.WATCH:
            return "Wait for stronger confirmation from real data before considering a trade."
        if decision == DecisionAction.AVOID:
            return "Do not enter while risk veto or data quality concerns remain unresolved."
        return "No new entry plan; monitor for improved evidence."

    def _invalidation_conditions(self, stop_loss: float | None) -> list[str]:
        conditions = ["Material negative news or data quality deterioration."]
        if stop_loss is not None:
            conditions.insert(0, f"Close below stop reference near {stop_loss}.")
        return conditions

    def _final_explanation(self, decision: DecisionAction, risk: RiskManagerOutput) -> str:
        if risk.veto:
            return f"Risk Manager veto applied: {risk.veto_reason}"
        if decision == DecisionAction.WATCH:
            return "Specialist evidence is not strong enough for a BUY under Phase 1 mock-data conditions."
        return "Decision Committee combined specialist agents and risk controls into the final decision."
