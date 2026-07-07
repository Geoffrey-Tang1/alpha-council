import os

from app.data_providers.base import MarketDataProvider
from app.data_providers.mock_provider import MockDataProvider
from app.data_providers.yfinance_provider import YFinanceDataProvider


def get_data_provider() -> MarketDataProvider:
    provider_name = os.getenv("DATA_PROVIDER", "mock").strip().lower()
    if provider_name == "mock":
        return MockDataProvider()
    if provider_name == "yfinance":
        return YFinanceDataProvider()

    return MockDataProvider(
        registry_warnings=[f"Unknown DATA_PROVIDER '{provider_name}'; falling back to mock data."]
    )
