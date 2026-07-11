from datetime import date

from fastapi import APIRouter, Query

from app.core.constants import MarketCode
from app.financial_data.schemas import (
    CompanyProfile,
    DataFetchResult,
    FinancialDataSnapshot,
    FinancialMetricSet,
    HistoricalPriceSeries,
    InstrumentIdentity,
    MarketQuote,
    ValuationMetricSet,
)
from app.services.financial_data_service import FinancialDataService

router = APIRouter(prefix="/financial-data", tags=["financial-data"])


@router.get("/status")
def financial_data_status() -> dict:
    service = FinancialDataService()
    health = service.health_check()
    return {
        "provider": health.source.provider,
        "availability_status": health.availability_status,
        "freshness_status": health.freshness_status,
        "capabilities": (health.payload or {}).get("capabilities", []),
        "status": (health.payload or {}).get("status", "unknown"),
        "quality": (health.payload or {}).get("quality", "unknown"),
        "warnings": health.warnings,
        "cache": service.cache_status(),
        "configuration": {
            "provider_selection": "backend environment only",
            "api_key_required": False,
            "api_key_returned_to_frontend": False,
        },
    }


@router.get("/instruments/resolve", response_model=InstrumentIdentity)
def resolve_instrument(ticker: str = Query(min_length=1), market: MarketCode = Query()) -> InstrumentIdentity:
    return FinancialDataService().resolve_instrument(ticker=ticker, market=market)


@router.get("/quote", response_model=MarketQuote)
def get_quote(ticker: str = Query(min_length=1), market: MarketCode = Query()) -> MarketQuote:
    return FinancialDataService().get_quote(ticker=ticker, market=market)


@router.get("/snapshot", response_model=FinancialDataSnapshot)
def get_snapshot(ticker: str = Query(min_length=1), market: MarketCode = Query()) -> FinancialDataSnapshot:
    return FinancialDataService().get_research_snapshot(ticker=ticker, market=market)


@router.get("/history", response_model=HistoricalPriceSeries)
def get_history(
    ticker: str = Query(min_length=1),
    market: MarketCode = Query(),
    start: date | None = None,
    end: date | None = None,
    interval: str = "1d",
) -> HistoricalPriceSeries:
    return FinancialDataService().get_price_history(ticker=ticker, market=market, start=start, end=end, interval=interval)


@router.get("/company-profile", response_model=CompanyProfile)
def get_company_profile(ticker: str = Query(min_length=1), market: MarketCode = Query()) -> CompanyProfile:
    return FinancialDataService().get_company_profile(ticker=ticker, market=market)


@router.get("/financial-metrics", response_model=FinancialMetricSet)
def get_financial_metrics(ticker: str = Query(min_length=1), market: MarketCode = Query()) -> FinancialMetricSet:
    return FinancialDataService().get_financial_metrics(ticker=ticker, market=market)


@router.get("/valuation-metrics", response_model=ValuationMetricSet)
def get_valuation_metrics(ticker: str = Query(min_length=1), market: MarketCode = Query()) -> ValuationMetricSet:
    return FinancialDataService().get_valuation_metrics(ticker=ticker, market=market)
