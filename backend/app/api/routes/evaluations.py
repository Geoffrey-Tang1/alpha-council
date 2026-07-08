from fastapi import APIRouter, HTTPException, Query

from app.core.constants import DecisionAction, MarketCode
from app.schemas.evaluations import (
    DirectionalResult,
    DecisionEvaluationResponse,
    EvaluationListResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationSummaryResponse,
)
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])
service = EvaluationService()


@router.post("/decision/{decision_id}", response_model=DecisionEvaluationResponse)
def evaluate_decision(decision_id: str) -> DecisionEvaluationResponse:
    evaluation = service.evaluate_decision(decision_id)
    if evaluation is None:
        raise HTTPException(status_code=404, detail="Decision not found.")
    return evaluation


@router.post("/run", response_model=EvaluationRunResponse)
def run_evaluations(payload: EvaluationRunRequest) -> EvaluationRunResponse:
    return service.run_evaluations(payload)


@router.get("/summary", response_model=EvaluationSummaryResponse)
def evaluation_summary() -> EvaluationSummaryResponse:
    return service.summary()


@router.get("", response_model=EvaluationListResponse)
def list_evaluations(
    ticker: str | None = None,
    market: MarketCode | None = None,
    decision: DecisionAction | None = None,
    directional_result: DirectionalResult | None = None,
    min_confidence: float | None = Query(default=None, ge=0, le=1),
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> EvaluationListResponse:
    return service.list_evaluations(
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


@router.get("/{evaluation_id}", response_model=DecisionEvaluationResponse)
def get_evaluation(evaluation_id: str) -> DecisionEvaluationResponse:
    evaluation = service.get_evaluation(evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found.")
    return evaluation
