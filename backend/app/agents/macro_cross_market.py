from app.agents.base import BaseAgent
from app.core.constants import AgentSignal
from app.schemas.agents import MacroAnalysisOutput


class MacroCrossMarketAgent(BaseAgent):
    name = "macro_cross_market"

    def analyze(self, collected_data: dict) -> MacroAnalysisOutput:
        macro = collected_data["macro_context"]
        return MacroAnalysisOutput(
            macro_signal=AgentSignal.WATCH,
            confidence=0.52,
            explanation=f"Phase 1 macro context is neutral: {macro.get('summary')}",
            macro_factors=[
                "Risk-on/risk-off environment is mocked.",
                "FX and sector rotation integrations are future work.",
            ],
            risks=["Macro data is placeholder logic in Phase 1."],
        )
