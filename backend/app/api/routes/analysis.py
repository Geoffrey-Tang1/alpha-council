from fastapi import APIRouter

from app.schemas.analysis import AnalysisRequest
from app.schemas.decisions import DecisionResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])
service = AnalysisService()


@router.post("/run", response_model=DecisionResponse)
def run_analysis(payload: AnalysisRequest) -> DecisionResponse:
    return service.run_analysis(payload)
