from app.agents.risk_manager import RiskManagerAgent
from app.core.constants import DecisionAction


def test_risk_manager_vetoes_buy_without_stop_loss():
    risk_manager = RiskManagerAgent()
    result = risk_manager.evaluate(
        collected_data={
            "latest_price": 100.0,
            "data_source_status": {"quality": "REAL", "provider_name": "yfinance"},
        },
        proposed_decision=DecisionAction.BUY,
        proposed_stop_loss=None,
    )

    assert result.veto is True
    assert result.veto_reason == "BUY requires a stop loss."
    assert result.max_position_size_pct == 0


def test_risk_manager_vetoes_missing_latest_price():
    risk_manager = RiskManagerAgent()
    result = risk_manager.evaluate(
        collected_data={
            "latest_price": None,
            "data_source_status": {"quality": "REAL", "provider_name": "yfinance"},
        },
        proposed_decision=DecisionAction.BUY,
        proposed_stop_loss=95.0,
    )

    assert result.veto is True
    assert "Missing latest price" in result.veto_reason


def test_risk_manager_blocks_buy_for_unavailable_data():
    risk_manager = RiskManagerAgent()
    result = risk_manager.evaluate(
        collected_data={
            "latest_price": 100.0,
            "data_source_status": {"quality": "UNAVAILABLE", "provider_name": "yfinance"},
        },
        proposed_decision=DecisionAction.BUY,
        proposed_stop_loss=95.0,
    )

    assert result.veto is True
    assert "Market data is unavailable" in result.veto_reason
    assert result.max_position_size_pct == 0


def test_risk_manager_blocks_buy_for_mock_data():
    risk_manager = RiskManagerAgent()
    result = risk_manager.evaluate(
        collected_data={
            "latest_price": 100.0,
            "data_source_status": {"quality": "MOCK", "provider_name": "mock", "is_mock": True},
        },
        proposed_decision=DecisionAction.BUY,
        proposed_stop_loss=95.0,
    )

    assert result.veto is True
    assert result.veto_reason == "BUY is blocked while using MOCK data."
