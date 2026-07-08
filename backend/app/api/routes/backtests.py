from fastapi import APIRouter, HTTPException, Query

from app.schemas.backtests import BacktestListResponse, BacktestResponse, BacktestRunRequest
from app.services.backtest_service import BacktestService

router = APIRouter(prefix="/backtests", tags=["backtests"])
service = BacktestService()


@router.post("/run", response_model=BacktestResponse)
def run_backtest(payload: BacktestRunRequest) -> BacktestResponse:
    return service.run_backtest(payload)


@router.get("", response_model=BacktestListResponse)
def list_backtests(limit: int = Query(default=50, ge=1, le=200)) -> BacktestListResponse:
    return service.list_backtests(limit=limit)


@router.get("/{backtest_id}", response_model=BacktestResponse)
def get_backtest(backtest_id: str) -> BacktestResponse:
    backtest = service.get_backtest(backtest_id)
    if backtest is None:
        raise HTTPException(status_code=404, detail="Backtest not found.")
    return backtest
