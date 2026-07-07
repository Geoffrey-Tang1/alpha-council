from app.agents.base import BaseAgent
from app.core.constants import AgentSignal
from app.schemas.agents import FundamentalAnalysisOutput


class FundamentalAnalysisAgent(BaseAgent):
    name = "fundamental_analysis"

    def analyze(self, collected_data: dict) -> FundamentalAnalysisOutput:
        metrics = collected_data["fundamentals"]
        revenue_growth = float(metrics.get("revenue_growth_yoy", 0))
        operating_margin = float(metrics.get("operating_margin", 0))
        debt_to_equity = float(metrics.get("debt_to_equity", 1))

        if revenue_growth > 0.12 and operating_margin > 0.2 and debt_to_equity < 0.6:
            signal = AgentSignal.BUY
            confidence = 0.61
            explanation = "Mock fundamentals show growth, profitability, and manageable leverage."
        elif debt_to_equity > 0.65:
            signal = AgentSignal.WATCH
            confidence = 0.5
            explanation = "Mock fundamentals are acceptable, but leverage requires monitoring."
        else:
            signal = AgentSignal.HOLD
            confidence = 0.56
            explanation = "Mock fundamentals are stable but not decisive enough for a strong view."

        return FundamentalAnalysisOutput(
            fundamental_signal=signal,
            confidence=confidence,
            explanation=explanation,
            key_metrics=metrics,
            risks=["Fundamental data is deterministic mock data in Phase 1."],
        )
