from fastapi import APIRouter, HTTPException, Query

from app.schemas.decisions import DecisionListResponse, DecisionResponse
from app.services.decision_service import DecisionService

router = APIRouter(prefix="/decisions", tags=["decisions"])
service = DecisionService()


@router.get("", response_model=DecisionListResponse)
def list_decisions(limit: int = Query(default=100, ge=1, le=500)) -> DecisionListResponse:
    return service.list_decisions(limit=limit)


@router.get("/{decision_id}", response_model=DecisionResponse)
def get_decision(decision_id: str) -> DecisionResponse:
    decision = service.get_decision(decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found.")
    return decision
