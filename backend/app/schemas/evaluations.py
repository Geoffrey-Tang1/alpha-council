from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.constants import DecisionAction, MarketCode


EVALUATION_DISCLAIMER = "Decision evaluation is historical and observational only. It does not prove future profitability."


class EvaluationStatus(StrEnum):
    PENDING = "PENDING"
    EVALUATED = "EVALUATED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"


class DirectionalResult(StrEnum):
    FAVORABLE = "FAVORABLE"
    UNFAVORABLE = "UNFAVORABLE"
    NEUTRAL_MONITORING = "NEUTRAL_MONITORING"
    NEUTRAL_HOLD = "NEUTRAL_HOLD"
    MISSED_UPSIDE = "MISSED_UPSIDE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"


class DecisionEvaluationResponse(BaseModel):
    evaluation_id: str
    decision_id: str
    ticker: str
    company_name: str = "Unknown Company"
    normalized_ticker: str = ""
    display_symbol: str = ""
    market: MarketCode
    decision: DecisionAction
    confidence: float = Field(ge=0, le=1)
    decision_timestamp: str
    decision_price: float | None
    evaluation_status: EvaluationStatus
    forward_return_1d: float | None
    forward_return_5d: float | None
    forward_return_20d: float | None
    forward_return_60d: float | None
    max_drawdown_20d: float | None
    max_drawdown_60d: float | None
    max_runup_20d: float | None
    max_runup_60d: float | None
    directional_result: DirectionalResult
    evaluation_summary: str
    data_provider: str
    data_quality: str
    data_disclaimer: str
    data_warnings: list[str]
    evaluation_disclaimer: str = EVALUATION_DISCLAIMER
    evaluated_at: str


class EvaluationListResponse(BaseModel):
    items: list[DecisionEvaluationResponse]
    total: int
    limit: int
    offset: int


class EvaluationRunRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=500)
    include_already_evaluated: bool = False


class EvaluationRunResponse(BaseModel):
    evaluated_count: int
    skipped_count: int
    error_count: int
    items: list[DecisionEvaluationResponse]
    disclaimer: str = EVALUATION_DISCLAIMER


class EvaluationSummaryResponse(BaseModel):
    total_evaluated: int
    favorable_count: int
    unfavorable_count: int
    neutral_count: int
    insufficient_data_count: int
    average_forward_return_1d: float | None
    average_forward_return_5d: float | None
    average_forward_return_20d: float | None
    average_forward_return_60d: float | None
    average_forward_return_by_decision: dict[str, dict[str, float | None]]
    average_forward_return_by_market: dict[str, dict[str, float | None]]
    average_forward_return_by_confidence_bucket: dict[str, dict[str, float | None]]
    favorable_rate_by_decision: dict[str, float | None]
    favorable_rate_by_market: dict[str, float | None]
    favorable_rate_by_confidence_bucket: dict[str, float | None]
    last_evaluated_at: str | None
    warning: str | None
    disclaimer: str = EVALUATION_DISCLAIMER
