from app.core.config import settings
from app.data_providers.base import MarketDataProvider
from app.data_providers.mock_provider import MockDataProvider


def get_data_provider() -> MarketDataProvider:
    if settings.data_provider != "mock":
        # Future providers should be selected here without changing agent logic.
        return MockDataProvider()
    return MockDataProvider()
