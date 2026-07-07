from fastapi import APIRouter

from app.schemas.market import MarketStatusResponse
from app.services.market_status_service import MarketStatusService

router = APIRouter(prefix="/market-status", tags=["market-status"])
service = MarketStatusService()


@router.get("", response_model=MarketStatusResponse)
def get_market_status() -> MarketStatusResponse:
    return service.get_all_market_statuses()
