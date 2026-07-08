from datetime import date, datetime, timedelta, timezone
from statistics import mean
from uuid import uuid4

import pandas as pd

from app.core.constants import DecisionAction, MarketCode
from app.data_providers.base import MarketDataProvider
from app.data_providers.provider_registry import get_data_provider
from app.db.repositories.decision_repository import DecisionRepository
from app.db.repositories.evaluation_repository import EvaluationRepository
from app.schemas.decisions import DecisionResponse
from app.schemas.evaluations import (
    DirectionalResult,
    EVALUATION_DISCLAIMER,
    DecisionEvaluationResponse,
    EvaluationListResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationStatus,
    EvaluationSummaryResponse,
)


FORWARD_WINDOWS = (1, 5, 20, 60)
MIN_EVALUATION_SAMPLE_SIZE = 30
AVOID_MISSED_UPSIDE_THRESHOLD = 0.05


class EvaluationService:
    def __init__(
        self,
        provider: MarketDataProvider | None = None,
        decision_repository: DecisionRepository | None = None,
        evaluation_repository: EvaluationRepository | None = None,
    ) -> None:
        self.provider = provider or get_data_provider()
        self.decision_repository = decision_repository or DecisionRepository()
        self.evaluation_repository = evaluation_repository or EvaluationRepository()

    def evaluate_decision(self, decision_id: str) -> DecisionEvaluationResponse | None:
        decision = self.decision_repository.get_by_id(decision_id)
        if decision is None:
            return None
        evaluation = self._evaluate(decision)
        return self.evaluation_repository.save(evaluation)

    def run_evaluations(self, payload: EvaluationRunRequest) -> EvaluationRunResponse:
        decisions = self.decision_repository.list(limit=payload.limit)
        items: list[DecisionEvaluationResponse] = []
        skipped_count = 0
        error_count = 0

        for decision in decisions:
            if not payload.include_already_evaluated and self.evaluation_repository.get_latest_for_decision(
                decision.decision_id
            ):
                skipped_count += 1
                continue

            try:
                evaluation = self._evaluate(decision)
                saved = self.evaluation_repository.save(evaluation)
                items.append(saved)
                if saved.evaluation_status == EvaluationStatus.ERROR:
                    error_count += 1
            except Exception:  # pragma: no cover - defensive guard for provider-specific failures.
                error_count += 1

        return EvaluationRunResponse(
            evaluated_count=len(items),
            skipped_count=skipped_count,
            error_count=error_count,
            items=items,
        )

    def list_evaluations(
        self,
        ticker: str | None = None,
        market: MarketCode | None = None,
        decision: DecisionAction | None = None,
        directional_result: DirectionalResult | None = None,
        min_confidence: float | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> EvaluationListResponse:
        items, total = self.evaluation_repository.list(
            ticker=ticker,
            market=market,
            decision=decision,
            directional_result=directional_result,
            min_confidence=min_confidence,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        return EvaluationListResponse(items=items, total=total, limit=limit, offset=offset)

    def get_evaluation(self, evaluation_id: str) -> DecisionEvaluationResponse | None:
        return self.evaluation_repository.get_by_id(evaluation_id)

    def summary(self) -> EvaluationSummaryResponse:
        evaluations = self.evaluation_repository.list_all()
        total = len(evaluations)
        favorable_count = sum(item.directional_result == DirectionalResult.FAVORABLE for item in evaluations)
        unfavorable_count = sum(
            item.directional_result in {DirectionalResult.UNFAVORABLE, DirectionalResult.MISSED_UPSIDE}
            for item in evaluations
        )
        neutral_count = sum(
            item.directional_result
            in {DirectionalResult.NEUTRAL_MONITORING, DirectionalResult.NEUTRAL_HOLD, DirectionalResult.UNKNOWN}
            for item in evaluations
        )
        insufficient_count = sum(
            item.directional_result == DirectionalResult.INSUFFICIENT_DATA
            or item.evaluation_status == EvaluationStatus.INSUFFICIENT_DATA
            for item in evaluations
        )

        warning = None
        if total < MIN_EVALUATION_SAMPLE_SIZE:
            warning = "Small sample size. Evaluation results may not be statistically meaningful."

        return EvaluationSummaryResponse(
            total_evaluated=total,
            favorable_count=favorable_count,
            unfavorable_count=unfavorable_count,
            neutral_count=neutral_count,
            insufficient_data_count=insufficient_count,
            average_forward_return_1d=self._average([item.forward_return_1d for item in evaluations]),
            average_forward_return_5d=self._average([item.forward_return_5d for item in evaluations]),
            average_forward_return_20d=self._average([item.forward_return_20d for item in evaluations]),
            average_forward_return_60d=self._average([item.forward_return_60d for item in evaluations]),
            average_forward_return_by_decision=self._average_returns_by_group(evaluations, lambda item: item.decision.value),
            average_forward_return_by_market=self._average_returns_by_group(evaluations, lambda item: item.market.value),
            average_forward_return_by_confidence_bucket=self._average_returns_by_group(
                evaluations, lambda item: self._confidence_bucket(item.confidence)
            ),
            favorable_rate_by_decision=self._favorable_rate_by_group(evaluations, lambda item: item.decision.value),
            favorable_rate_by_market=self._favorable_rate_by_group(evaluations, lambda item: item.market.value),
            favorable_rate_by_confidence_bucket=self._favorable_rate_by_group(
                evaluations, lambda item: self._confidence_bucket(item.confidence)
            ),
            last_evaluated_at=max((item.evaluated_at for item in evaluations), default=None),
            warning=warning,
        )

    def _evaluate(self, decision: DecisionResponse) -> DecisionEvaluationResponse:
        evaluated_at = datetime.now(timezone.utc).isoformat()
        decision_date = self._decision_date(decision.timestamp)
        end_date = self._evaluation_end_date(decision_date)

        try:
            history = self.provider.get_price_history(
                ticker=decision.ticker,
                market=decision.market,
                start=decision_date - timedelta(days=10),
                end=end_date,
            )
            source_status = self.provider.get_data_source_status()
            prepared = self._prepare_history(history)
            return self._build_evaluation(
                decision=decision,
                history=prepared,
                source_status=source_status,
                evaluated_at=evaluated_at,
                decision_date=decision_date,
            )
        except Exception as exc:  # pragma: no cover - exact provider exceptions vary.
            return self._error_evaluation(decision=decision, evaluated_at=evaluated_at, error=str(exc))

    def _build_evaluation(
        self,
        decision: DecisionResponse,
        history: pd.DataFrame,
        source_status: dict,
        evaluated_at: str,
        decision_date: date,
    ) -> DecisionEvaluationResponse:
        data_provider = source_status.get("provider_name", "mock")
        data_quality = str(source_status.get("quality", "UNAVAILABLE")).upper()
        data_warnings = list(source_status.get("warnings", []))

        if history.empty:
            return self._insufficient_evaluation(
                decision=decision,
                evaluated_at=evaluated_at,
                data_provider=data_provider,
                data_quality="UNAVAILABLE",
                data_warnings=[*data_warnings, "No usable price history was available after the decision date."],
            )

        candidates = history[history["date"] >= decision_date].reset_index(drop=True)
        if candidates.empty:
            return self._insufficient_evaluation(
                decision=decision,
                evaluated_at=evaluated_at,
                data_provider=data_provider,
                data_quality="UNAVAILABLE",
                data_warnings=[*data_warnings, "No price rows were available at or after the decision date."],
            )

        anchor_price = self._safe_float(candidates.loc[0, "close"])
        if anchor_price is None or anchor_price <= 0:
            return self._insufficient_evaluation(
                decision=decision,
                evaluated_at=evaluated_at,
                data_provider=data_provider,
                data_quality="UNAVAILABLE",
                data_warnings=[*data_warnings, "The decision anchor price was missing or invalid."],
            )

        returns = self._forward_returns(candidates=candidates, anchor_price=anchor_price)
        max_drawdown_20d = self._window_extreme(candidates, anchor_price, window=20, mode="min")
        max_drawdown_60d = self._window_extreme(candidates, anchor_price, window=60, mode="min")
        max_runup_20d = self._window_extreme(candidates, anchor_price, window=20, mode="max")
        max_runup_60d = self._window_extreme(candidates, anchor_price, window=60, mode="max")

        has_any_forward_return = any(value is not None for value in returns.values())
        if not has_any_forward_return:
            return self._insufficient_evaluation(
                decision=decision,
                evaluated_at=evaluated_at,
                data_provider=data_provider,
                data_quality=data_quality,
                data_warnings=[*data_warnings, "Not enough future rows were available to calculate a 1-day return."],
                decision_price=anchor_price,
            )

        if data_provider == "yfinance" and len(candidates) < 61 and data_quality == "REAL":
            data_quality = "DEGRADED"
            data_warnings.append("Fewer than 60 forward trading rows were available from yfinance.")

        directional_result = self._directional_result(decision.decision, returns)
        return DecisionEvaluationResponse(
            evaluation_id=f"eval_{uuid4().hex}",
            decision_id=decision.decision_id,
            ticker=decision.ticker,
            market=decision.market,
            decision=decision.decision,
            confidence=decision.confidence,
            decision_timestamp=decision.timestamp,
            decision_price=round(anchor_price, 6),
            evaluation_status=EvaluationStatus.EVALUATED,
            forward_return_1d=returns[1],
            forward_return_5d=returns[5],
            forward_return_20d=returns[20],
            forward_return_60d=returns[60],
            max_drawdown_20d=max_drawdown_20d,
            max_drawdown_60d=max_drawdown_60d,
            max_runup_20d=max_runup_20d,
            max_runup_60d=max_runup_60d,
            directional_result=directional_result,
            evaluation_summary=self._summary_text(decision.decision, directional_result, returns),
            data_provider=data_provider,
            data_quality=data_quality,
            data_disclaimer=self._data_disclaimer(data_provider=data_provider, data_quality=data_quality),
            data_warnings=list(dict.fromkeys(data_warnings)),
            evaluated_at=evaluated_at,
        )

    def _prepare_history(self, history: pd.DataFrame) -> pd.DataFrame:
        if history is None or history.empty:
            return pd.DataFrame(columns=["date", "close"])
        prepared = history.copy()
        if "date" not in prepared or "close" not in prepared:
            return pd.DataFrame(columns=["date", "close"])
        prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce").dt.date
        prepared["close"] = pd.to_numeric(prepared["close"], errors="coerce")
        return prepared.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)

    def _forward_returns(self, candidates: pd.DataFrame, anchor_price: float) -> dict[int, float | None]:
        returns: dict[int, float | None] = {}
        for window in FORWARD_WINDOWS:
            if len(candidates) <= window:
                returns[window] = None
                continue
            close = self._safe_float(candidates.loc[window, "close"])
            returns[window] = round(close / anchor_price - 1, 6) if close is not None else None
        return returns

    def _window_extreme(
        self,
        candidates: pd.DataFrame,
        anchor_price: float,
        window: int,
        mode: str,
    ) -> float | None:
        if len(candidates) <= 1:
            return None
        closes = candidates.loc[1:window, "close"].dropna()
        if closes.empty:
            return None
        returns = closes / anchor_price - 1
        value = returns.min() if mode == "min" else returns.max()
        return round(float(value), 6)

    def _directional_result(
        self,
        decision: DecisionAction,
        returns: dict[int, float | None],
    ) -> DirectionalResult:
        primary_return = self._primary_return(returns)
        if primary_return is None:
            return DirectionalResult.INSUFFICIENT_DATA

        if decision == DecisionAction.BUY:
            return DirectionalResult.FAVORABLE if primary_return > 0 else DirectionalResult.UNFAVORABLE
        if decision == DecisionAction.SELL:
            return DirectionalResult.FAVORABLE if primary_return < 0 else DirectionalResult.UNFAVORABLE
        if decision == DecisionAction.WATCH:
            return DirectionalResult.NEUTRAL_MONITORING
        if decision == DecisionAction.HOLD:
            return DirectionalResult.NEUTRAL_HOLD
        if decision == DecisionAction.AVOID:
            if primary_return > AVOID_MISSED_UPSIDE_THRESHOLD:
                return DirectionalResult.MISSED_UPSIDE
            return DirectionalResult.FAVORABLE
        return DirectionalResult.UNKNOWN

    def _insufficient_evaluation(
        self,
        decision: DecisionResponse,
        evaluated_at: str,
        data_provider: str,
        data_quality: str,
        data_warnings: list[str],
        decision_price: float | None = None,
    ) -> DecisionEvaluationResponse:
        return DecisionEvaluationResponse(
            evaluation_id=f"eval_{uuid4().hex}",
            decision_id=decision.decision_id,
            ticker=decision.ticker,
            market=decision.market,
            decision=decision.decision,
            confidence=decision.confidence,
            decision_timestamp=decision.timestamp,
            decision_price=decision_price,
            evaluation_status=EvaluationStatus.INSUFFICIENT_DATA,
            forward_return_1d=None,
            forward_return_5d=None,
            forward_return_20d=None,
            forward_return_60d=None,
            max_drawdown_20d=None,
            max_drawdown_60d=None,
            max_runup_20d=None,
            max_runup_60d=None,
            directional_result=DirectionalResult.INSUFFICIENT_DATA,
            evaluation_summary="Insufficient future price data to evaluate this saved decision.",
            data_provider=data_provider,
            data_quality=data_quality,
            data_disclaimer=self._data_disclaimer(data_provider=data_provider, data_quality=data_quality),
            data_warnings=list(dict.fromkeys(data_warnings)),
            evaluated_at=evaluated_at,
        )

    def _error_evaluation(self, decision: DecisionResponse, evaluated_at: str, error: str) -> DecisionEvaluationResponse:
        return DecisionEvaluationResponse(
            evaluation_id=f"eval_{uuid4().hex}",
            decision_id=decision.decision_id,
            ticker=decision.ticker,
            market=decision.market,
            decision=decision.decision,
            confidence=decision.confidence,
            decision_timestamp=decision.timestamp,
            decision_price=None,
            evaluation_status=EvaluationStatus.ERROR,
            forward_return_1d=None,
            forward_return_5d=None,
            forward_return_20d=None,
            forward_return_60d=None,
            max_drawdown_20d=None,
            max_drawdown_60d=None,
            max_runup_20d=None,
            max_runup_60d=None,
            directional_result=DirectionalResult.UNKNOWN,
            evaluation_summary="Decision evaluation failed before returns could be calculated.",
            data_provider=getattr(self.provider, "provider_name", "unknown"),
            data_quality="UNAVAILABLE",
            data_disclaimer=self._data_disclaimer(data_provider="unknown", data_quality="UNAVAILABLE"),
            data_warnings=[f"Evaluation error: {error}", EVALUATION_DISCLAIMER],
            evaluated_at=evaluated_at,
        )

    def _summary_text(
        self,
        decision: DecisionAction,
        directional_result: DirectionalResult,
        returns: dict[int, float | None],
    ) -> str:
        primary_return = self._primary_return(returns)
        formatted_return = "N/A" if primary_return is None else f"{primary_return:.2%}"
        return (
            f"{decision.value} decision evaluated as {directional_result.value} using available forward rows. "
            f"Primary available forward return: {formatted_return}. {EVALUATION_DISCLAIMER}"
        )

    def _evaluation_end_date(self, decision_date: date) -> date:
        if getattr(self.provider, "provider_name", "") == "mock":
            return decision_date + timedelta(days=140)
        return min(date.today(), decision_date + timedelta(days=140))

    def _primary_return(self, returns: dict[int, float | None]) -> float | None:
        for window in (20, 5, 1, 60):
            value = returns.get(window)
            if value is not None:
                return value
        return None

    def _decision_date(self, timestamp: str) -> date:
        normalized = timestamp.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).date()

    def _safe_float(self, value) -> float | None:
        try:
            if pd.isna(value):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _data_disclaimer(self, data_provider: str, data_quality: str) -> str:
        if data_provider == "mock" or data_quality == "MOCK":
            return "MVP Mode: using deterministic mock data. Not real market data."
        if data_provider == "yfinance" and data_quality == "REAL":
            return "Market data provided by yfinance. Data may be delayed, incomplete, or adjusted. Not financial advice."
        if data_quality == "DEGRADED":
            return "Market data provider degraded. Some data may be incomplete or fallback mock data. Not financial advice."
        return "Market data unavailable or insufficient for evaluation. Not financial advice."

    def _average(self, values: list[float | None]) -> float | None:
        clean_values = [value for value in values if value is not None]
        if not clean_values:
            return None
        return round(mean(clean_values), 6)

    def _average_returns_by_group(
        self,
        evaluations: list[DecisionEvaluationResponse],
        key_fn,
    ) -> dict[str, dict[str, float | None]]:
        grouped: dict[str, list[DecisionEvaluationResponse]] = {}
        for item in evaluations:
            grouped.setdefault(key_fn(item), []).append(item)

        return {
            key: {
                "1d": self._average([item.forward_return_1d for item in items]),
                "5d": self._average([item.forward_return_5d for item in items]),
                "20d": self._average([item.forward_return_20d for item in items]),
                "60d": self._average([item.forward_return_60d for item in items]),
            }
            for key, items in grouped.items()
        }

    def _favorable_rate_by_group(self, evaluations: list[DecisionEvaluationResponse], key_fn) -> dict[str, float | None]:
        grouped: dict[str, list[DecisionEvaluationResponse]] = {}
        for item in evaluations:
            grouped.setdefault(key_fn(item), []).append(item)

        rates: dict[str, float | None] = {}
        for key, items in grouped.items():
            eligible = [
                item
                for item in items
                if item.directional_result
                in {DirectionalResult.FAVORABLE, DirectionalResult.UNFAVORABLE, DirectionalResult.MISSED_UPSIDE}
            ]
            rates[key] = None if not eligible else round(
                sum(item.directional_result == DirectionalResult.FAVORABLE for item in eligible) / len(eligible),
                6,
            )
        return rates

    def _confidence_bucket(self, confidence: float) -> str:
        if confidence < 0.4:
            return "0.0-0.4"
        if confidence < 0.6:
            return "0.4-0.6"
        if confidence < 0.8:
            return "0.6-0.8"
        return "0.8-1.0"
