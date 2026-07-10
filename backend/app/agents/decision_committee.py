from datetime import datetime, timezone
from uuid import uuid4

from app.agents.base import BaseAgent
from app.core.constants import AgentSignal, DecisionAction
from app.data_providers.instrument_metadata import build_instrument_metadata
from app.schemas.agents import (
    AgentOutputs,
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
        raw_data_quality = str(collected_data.get("data_source_status", {}).get("quality", "UNAVAILABLE")).upper()
        if risk.veto and raw_data_quality == "UNAVAILABLE":
            final_decision = DecisionAction.AVOID
        elif risk.veto:
            final_decision = DecisionAction.WATCH
        elif raw_data_quality in {"MOCK", "DEGRADED"}:
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

        data_source_status = collected_data["data_source_status"]
        data_provider = data_source_status.get("provider_name", "mock")
        data_quality = data_source_status.get("quality", "UNAVAILABLE").upper()
        data_disclaimer = self._data_disclaimer(data_provider=data_provider, data_quality=data_quality)
        data_warnings = [
            data_disclaimer,
            *data_source_status.get("warnings", []),
        ]
        company_profile = collected_data.get("company_profile", {})
        metadata = build_instrument_metadata(
            ticker=collected_data["ticker"],
            market=collected_data["market"],
            company_name=company_profile.get("company_name"),
        )

        return DecisionResponse(
            decision_id=f"dec_{uuid4().hex}",
            ticker=collected_data["ticker"],
            company_name=metadata["company_name"],
            normalized_ticker=metadata["normalized_ticker"],
            display_symbol=metadata["display_symbol"],
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
            agent_outputs=AgentOutputs(
                technical_analysis=technical,
                fundamental_analysis=fundamental,
                news_sentiment=news,
                macro_cross_market=macro,
                risk_manager=risk,
                portfolio_manager=portfolio,
            ),
            final_explanation=self._final_explanation(final_decision, risk),
            data_sources=[
                DataSource(
                    name=data_provider,
                    type="market_data",
                    status=data_source_status.get("status", data_quality),
                )
            ],
            data_provider=data_provider,
            data_quality=data_quality,
            data_disclaimer=data_disclaimer,
            data_warnings=list(dict.fromkeys(data_warnings)),
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
            return "Specialist evidence or data-quality controls are not strong enough for a BUY."
        return "Decision Committee combined specialist agents and risk controls into the final decision."

    def _data_disclaimer(self, data_provider: str, data_quality: str) -> str:
        if data_provider == "mock" or data_quality == "MOCK":
            return "MVP Mode: using deterministic mock data. Not real market data."
        if data_provider == "yfinance" and data_quality == "REAL":
            return "Market data provided by yfinance. Data may be delayed, incomplete, or adjusted. Not financial advice."
        if data_quality == "DEGRADED":
            return "Market data provider degraded. Some data may be incomplete or fallback mock data. Not financial advice."
        return "Market data unavailable. Wisoka Compass cannot validate this decision. Not financial advice."
