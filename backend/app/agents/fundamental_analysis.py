from app.agents.base import BaseAgent
from app.core.constants import AgentSignal
from app.schemas.agents import FundamentalAnalysisOutput


class FundamentalAnalysisAgent(BaseAgent):
    name = "fundamental_analysis"

    def analyze(self, collected_data: dict) -> FundamentalAnalysisOutput:
        metrics = collected_data["fundamentals"]
        is_mock = bool(metrics.get("is_mock", False))
        revenue_growth = self._safe_float(metrics.get("revenue_growth_yoy", metrics.get("revenue_growth")), 0)
        operating_margin = self._safe_float(metrics.get("operating_margin", metrics.get("profit_margins")), 0)
        debt_to_equity = self._safe_float(metrics.get("debt_to_equity"), 1)

        if revenue_growth > 0.12 and operating_margin > 0.2 and debt_to_equity < 0.6:
            signal = AgentSignal.BUY
            confidence = 0.61
            explanation = "Fundamental snapshot shows growth, profitability, and manageable leverage."
        elif debt_to_equity > 0.65:
            signal = AgentSignal.WATCH
            confidence = 0.5
            explanation = "Fundamental snapshot is acceptable, but leverage requires monitoring."
        else:
            signal = AgentSignal.HOLD
            confidence = 0.56
            explanation = "Fundamental snapshot is stable but not decisive enough for a strong view."

        risks = (
            ["Fundamental data is deterministic mock data."]
            if is_mock
            else ["Fundamental data from yfinance may be incomplete, delayed, or unavailable for some markets."]
        )

        return FundamentalAnalysisOutput(
            fundamental_signal=signal,
            confidence=confidence,
            explanation=explanation,
            key_metrics=metrics,
            risks=risks,
        )

    def _safe_float(self, value, default: float) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default
