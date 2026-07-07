from fastapi import APIRouter, Query

from app.schemas.decisions import DecisionListResponse
from app.services.decision_service import DecisionService

router = APIRouter(prefix="/decisions", tags=["decisions"])
service = DecisionService()


@router.get("", response_model=DecisionListResponse)
def list_decisions(limit: int = Query(default=100, ge=1, le=500)) -> DecisionListResponse:
    return service.list_decisions(limit=limit)
