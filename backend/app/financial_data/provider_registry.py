import os

from app.data_providers.base import MarketDataProvider
from app.data_providers.provider_registry import get_data_provider
from app.financial_data.adapters.base import FinancialDataProviderAdapter
from app.financial_data.adapters.disabled import DisabledFinancialDataAdapter
from app.financial_data.adapters.legacy_market_data import LegacyMarketDataFinancialAdapter


def get_financial_data_adapter(provider: MarketDataProvider | None = None) -> FinancialDataProviderAdapter:
    selected = os.getenv("FINANCIAL_DATA_PROVIDER", "auto").strip().lower()
    if selected == "disabled":
        return DisabledFinancialDataAdapter()

    # "auto" intentionally reuses the active DATA_PROVIDER so existing mock and
    # yfinance modes stay compatible with backtests, evaluation, and tests.
    active_provider = provider or get_data_provider()
    return LegacyMarketDataFinancialAdapter(active_provider)

