from app.agents.base import BaseAgent
from app.core.constants import AgentSignal
from app.schemas.agents import (
    BullCaseOutput,
    FundamentalAnalysisOutput,
    MacroAnalysisOutput,
    NewsSentimentOutput,
    TechnicalAnalysisOutput,
)


class BullCaseAgent(BaseAgent):
    name = "bull_case"

    def analyze(
        self,
        technical: TechnicalAnalysisOutput,
        fundamental: FundamentalAnalysisOutput,
        news: NewsSentimentOutput,
        macro: MacroAnalysisOutput,
    ) -> BullCaseOutput:
        points: list[str] = []
        evidence: list[str] = []

        if technical.technical_signal in {AgentSignal.BUY, AgentSignal.HOLD}:
            points.append("Technical setup is not broken.")
            evidence.append(technical.explanation)
        if fundamental.fundamental_signal in {AgentSignal.BUY, AgentSignal.HOLD}:
            points.append("Mock fundamentals do not show an obvious quality failure.")
            evidence.append(fundamental.explanation)
        if news.sentiment_signal != AgentSignal.AVOID:
            points.append("No severe negative catalyst is present in mock news.")
        if macro.macro_signal != AgentSignal.AVOID:
            points.append("Macro placeholder context is not outright hostile.")

        return BullCaseOutput(
            bull_points=points or ["There is not enough evidence for a strong bull case."],
            supporting_evidence=evidence or ["Specialist agents did not provide strong positive evidence."],
            assumptions=[
                "Phase 1 mock data roughly represents current market conditions.",
                "No live broker or real-time news feed is connected.",
            ],
            confidence=round((technical.confidence + fundamental.confidence + news.confidence + macro.confidence) / 4, 2),
        )
