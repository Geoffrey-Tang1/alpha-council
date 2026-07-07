from app.agents.base import BaseAgent
from app.core.constants import DecisionAction
from app.schemas.agents import RiskManagerOutput, TechnicalAnalysisOutput


class RiskManagerAgent(BaseAgent):
    name = "risk_manager"

    def evaluate(
        self,
        collected_data: dict,
        technical: TechnicalAnalysisOutput | None = None,
        proposed_decision: DecisionAction | None = None,
        proposed_stop_loss: float | None = None,
    ) -> RiskManagerOutput:
        warnings: list[str] = ["No decision is guaranteed; AlphaCouncil is research support only."]
        latest_price = collected_data.get("latest_price")
        data_source_status = collected_data.get("data_source_status", {})
        is_mock = bool(data_source_status.get("is_mock"))

        veto = False
        veto_reason = None
        risk_level = "MEDIUM"
        max_position_size_pct = 5.0
        confidence_adjustment = 0.0

        if latest_price is None:
            veto = True
            veto_reason = "Missing latest price prevents risk validation."
            risk_level = "UNKNOWN"
            max_position_size_pct = 0.0
            confidence_adjustment = -0.4

        if proposed_decision == DecisionAction.BUY and proposed_stop_loss is None:
            veto = True
            veto_reason = "BUY requires a stop loss."
            risk_level = "HIGH"
            max_position_size_pct = 0.0
            confidence_adjustment = min(confidence_adjustment, -0.25)

        volatility = None
        if technical is not None:
            volatility = technical.key_indicators.get("volatility_20d")
        if volatility is not None and volatility > 0.35:
            warnings.append("High volatility detected; max position size reduced.")
            risk_level = "HIGH" if not veto else risk_level
            max_position_size_pct = min(max_position_size_pct, 3.0)
            confidence_adjustment -= 0.08

        if is_mock:
            warnings.append("Phase 1 uses mock market data; verify with real sources before acting.")

        return RiskManagerOutput(
            risk_level=risk_level,
            max_position_size_pct=max_position_size_pct,
            stop_loss_required=True,
            risk_warnings=warnings,
            veto=veto,
            veto_reason=veto_reason,
            confidence_adjustment=round(confidence_adjustment, 2),
        )
