from app.agents.base import BaseAgent
from app.core.constants import AgentSignal
from app.schemas.agents import (
    BearCaseOutput,
    FundamentalAnalysisOutput,
    MacroAnalysisOutput,
    NewsSentimentOutput,
    TechnicalAnalysisOutput,
)


class BearCaseAgent(BaseAgent):
    name = "bear_case"

    def analyze(
        self,
        technical: TechnicalAnalysisOutput,
        fundamental: FundamentalAnalysisOutput,
        news: NewsSentimentOutput,
        macro: MacroAnalysisOutput,
    ) -> BearCaseOutput:
        risk_factors = [*technical.risks, *fundamental.risks, *news.risks, *macro.risks]
        bear_points: list[str] = []

        if technical.technical_signal in {AgentSignal.SELL, AgentSignal.WATCH, AgentSignal.AVOID}:
            bear_points.append("Technical confirmation is not strong enough for an aggressive decision.")
        if fundamental.fundamental_signal in {AgentSignal.WATCH, AgentSignal.AVOID}:
            bear_points.append("Fundamental confidence is limited in Phase 1.")
        bear_points.append("Mock data limits confidence and should keep sizing conservative.")

        return BearCaseOutput(
            bear_points=bear_points,
            supporting_evidence=[technical.explanation, fundamental.explanation, news.explanation, macro.explanation],
            risk_factors=risk_factors,
            confidence=round(max(0.45, min(0.8, len(risk_factors) * 0.08 + 0.45)), 2),
        )
