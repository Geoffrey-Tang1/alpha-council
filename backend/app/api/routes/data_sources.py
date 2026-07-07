from fastapi import APIRouter

from app.data_providers.provider_registry import get_data_provider

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


@router.get("/status")
def get_data_source_status() -> dict:
    provider = get_data_provider()
    status = provider.get_data_source_status()
    data_provider = status.get("provider_name", "mock")
    data_quality = status.get("quality", "UNAVAILABLE")
    if data_provider == "mock":
        data_disclaimer = "MVP Mode: using deterministic mock data. Not real market data."
    elif data_provider == "yfinance":
        data_disclaimer = "Data provider: yfinance. Data may be delayed or incomplete."
    else:
        data_disclaimer = "Data provider status unknown."

    return {
        "data_provider": data_provider,
        "data_quality": data_quality,
        "data_disclaimer": data_disclaimer,
        "data_warnings": status.get("warnings", []),
    }
