from datetime import date
from uuid import uuid4

import pandas as pd

from app.core.constants import AgentSignal, DecisionAction, MarketCode, MarketStatus
from app.data_providers.base import MarketDataProvider
from app.db.repositories.decision_repository import DecisionRepository
from app.schemas.decisions import DecisionResponse
from app.schemas.evaluations import DirectionalResult, EvaluationStatus
from app.services.evaluation_service import EVALUATION_DISCLAIMER, EvaluationService


class StaticPriceProvider(MarketDataProvider):
    provider_name = "mock"

    def __init__(self, closes: list[float]) -> None:
        self.closes = closes

    def get_latest_price(self, ticker: str, market: MarketCode) -> float | None:
        return self.closes[-1] if self.closes else None

    def get_price_history(
        self,
        ticker: str,
        market: MarketCode,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        dates = pd.bdate_range("2023-01-02", periods=len(self.closes), freq="B")
        return pd.DataFrame(
            {
                "date": dates.date.astype(str),
                "open": self.closes,
                "high": [value * 1.01 for value in self.closes],
                "low": [value * 0.99 for value in self.closes],
                "close": self.closes,
                "volume": [1_000_000] * len(self.closes),
            }
        )

    def get_company_profile(self, ticker: str, market: MarketCode) -> dict:
        return {}

    def get_fundamentals(self, ticker: str, market: MarketCode) -> dict:
        return {}

    def get_news(self, ticker: str, market: MarketCode, limit: int = 5) -> list[dict]:
        return []

    def get_macro_context(self, market: MarketCode) -> dict:
        return {}

    def get_data_source_status(self) -> dict:
        return {
            "provider_name": "mock",
            "quality": "MOCK",
            "status": "OK",
            "warnings": ["MVP Mode: using deterministic mock data. Not real market data."],
        }


def make_decision(action: DecisionAction, confidence: float = 0.7, ticker: str | None = None) -> DecisionResponse:
    ticker = ticker or f"T{uuid4().hex[:5]}".upper()
    return DecisionResponse.model_validate(
        {
            "decision_id": f"dec_{uuid4().hex}",
            "ticker": ticker,
            "market": "US",
            "latest_price": 100,
            "market_status": "CLOSED",
            "decision": action.value,
            "confidence": confidence,
            "time_horizon": "swing",
            "entry_plan": "Test entry.",
            "stop_loss": 95,
            "take_profit": 110,
            "max_position_size_pct": 0,
            "bull_case": {
                "bull_points": ["test"],
                "supporting_evidence": ["test"],
                "assumptions": ["test"],
                "confidence": 0.5,
            },
            "bear_case": {
                "bear_points": ["test"],
                "supporting_evidence": ["test"],
                "risk_factors": ["test"],
                "confidence": 0.5,
            },
            "risk_warnings": ["test"],
            "invalidation_conditions": ["test"],
            "agent_votes": [{"agent": "test", "vote": action.value, "confidence": confidence}],
            "agent_outputs": {
                "technical_analysis": {
                    "technical_signal": AgentSignal.WATCH.value,
                    "confidence": 0.5,
                    "explanation": "test",
                    "key_indicators": {},
                    "risks": [],
                },
                "fundamental_analysis": {
                    "fundamental_signal": AgentSignal.WATCH.value,
                    "confidence": 0.5,
                    "explanation": "test",
                    "key_metrics": {},
                    "risks": [],
                },
                "news_sentiment": {
                    "sentiment_signal": AgentSignal.WATCH.value,
                    "confidence": 0.5,
                    "explanation": "test",
                    "catalysts": [],
                    "risks": [],
                    "data_sources": ["test"],
                },
                "macro_cross_market": {
                    "macro_signal": AgentSignal.WATCH.value,
                    "confidence": 0.5,
                    "explanation": "test",
                    "macro_factors": [],
                    "risks": [],
                },
                "risk_manager": {
                    "risk_level": "LOW",
                    "max_position_size_pct": 0,
                    "stop_loss_required": True,
                    "risk_warnings": [],
                    "veto": False,
                    "veto_reason": None,
                    "confidence_adjustment": 0,
                },
                "portfolio_manager": {
                    "portfolio_fit": "test",
                    "recommended_position_size_pct": 0,
                    "concentration_warning": None,
                    "explanation": "test",
                },
            },
            "final_explanation": "test",
            "data_sources": [{"name": "mock", "type": "market_data", "status": "OK"}],
            "data_provider": "mock",
            "data_quality": "MOCK",
            "data_disclaimer": "MVP Mode: using deterministic mock data. Not real market data.",
            "data_warnings": ["MVP Mode: using deterministic mock data. Not real market data."],
            "timestamp": "2023-01-02T12:00:00+00:00",
            "saved": False,
        }
    )


def test_evaluation_service_calculates_forward_returns_drawdown_and_runup():
    closes = [100, 101, 102, 98, 105, 110, *([111] * 55)]
    decision = DecisionRepository().save(make_decision(DecisionAction.BUY))
    service = EvaluationService(provider=StaticPriceProvider(closes=closes))

    evaluation = service.evaluate_decision(decision.decision_id)

    assert evaluation is not None
    assert evaluation.evaluation_status == EvaluationStatus.EVALUATED
    assert evaluation.forward_return_1d == 0.01
    assert evaluation.forward_return_5d == 0.1
    assert evaluation.forward_return_20d == 0.11
    assert evaluation.max_drawdown_20d == -0.02
    assert evaluation.max_runup_20d == 0.11
    assert evaluation.directional_result == DirectionalResult.FAVORABLE
    assert EVALUATION_DISCLAIMER in evaluation.evaluation_summary


def test_directional_result_logic_for_sell_watch_hold_and_avoid():
    rising_service = EvaluationService(provider=StaticPriceProvider(closes=[100, *([101] * 5), *([107] * 60)]))
    falling_service = EvaluationService(provider=StaticPriceProvider(closes=[100, *([99] * 5), *([93] * 60)]))

    sell_eval = falling_service.evaluate_decision(DecisionRepository().save(make_decision(DecisionAction.SELL)).decision_id)
    watch_eval = rising_service.evaluate_decision(DecisionRepository().save(make_decision(DecisionAction.WATCH)).decision_id)
    hold_eval = rising_service.evaluate_decision(DecisionRepository().save(make_decision(DecisionAction.HOLD)).decision_id)
    avoid_eval = rising_service.evaluate_decision(DecisionRepository().save(make_decision(DecisionAction.AVOID)).decision_id)

    assert sell_eval.directional_result == DirectionalResult.FAVORABLE
    assert watch_eval.directional_result == DirectionalResult.NEUTRAL_MONITORING
    assert hold_eval.directional_result == DirectionalResult.NEUTRAL_HOLD
    assert avoid_eval.directional_result == DirectionalResult.MISSED_UPSIDE


def test_insufficient_data_handling_is_persisted():
    decision = DecisionRepository().save(make_decision(DecisionAction.BUY))
    service = EvaluationService(provider=StaticPriceProvider(closes=[100]))

    evaluation = service.evaluate_decision(decision.decision_id)
    reloaded = service.get_evaluation(evaluation.evaluation_id)

    assert evaluation.evaluation_status == EvaluationStatus.INSUFFICIENT_DATA
    assert evaluation.directional_result == DirectionalResult.INSUFFICIENT_DATA
    assert evaluation.forward_return_1d is None
    assert reloaded is not None
    assert reloaded.evaluation_id == evaluation.evaluation_id


def test_evaluation_summary_aggregation_returns_grouped_metrics():
    decision = DecisionRepository().save(make_decision(DecisionAction.BUY, confidence=0.85))
    service = EvaluationService(provider=StaticPriceProvider(closes=[100, *([101] * 5), *([104] * 60)]))
    evaluation = service.evaluate_decision(decision.decision_id)

    summary = service.summary()

    assert summary.total_evaluated >= 1
    assert summary.favorable_count >= 1
    assert summary.average_forward_return_20d is not None
    assert "BUY" in summary.average_forward_return_by_decision
    assert "US" in summary.average_forward_return_by_market
    assert "0.8-1.0" in summary.average_forward_return_by_confidence_bucket
    assert summary.favorable_rate_by_decision["BUY"] is not None
    assert summary.last_evaluated_at >= evaluation.evaluated_at
