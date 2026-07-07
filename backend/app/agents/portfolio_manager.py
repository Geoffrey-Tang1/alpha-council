from app.agents.base import BaseAgent
from app.schemas.agents import PortfolioManagerOutput, RiskManagerOutput


class PortfolioManagerAgent(BaseAgent):
    name = "portfolio_manager"

    def evaluate(self, risk: RiskManagerOutput) -> PortfolioManagerOutput:
        if risk.veto:
            return PortfolioManagerOutput(
                portfolio_fit="not_fit",
                recommended_position_size_pct=0,
                concentration_warning="Risk veto prevents a new BUY decision.",
                explanation="Portfolio fit is blocked until risk validation passes.",
            )

        recommended_size = min(5.0, risk.max_position_size_pct)
        warning = None
        if recommended_size < 5.0:
            warning = "Position size reduced by risk controls."

        return PortfolioManagerOutput(
            portfolio_fit="acceptable_with_limits",
            recommended_position_size_pct=recommended_size,
            concentration_warning=warning,
            explanation="Phase 1 assumes no existing portfolio positions; sizing follows risk limits.",
        )
