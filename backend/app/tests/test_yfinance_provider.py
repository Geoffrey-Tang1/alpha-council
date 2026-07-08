import pandas as pd

from app.core.constants import MarketCode
from app.data_providers.yfinance_provider import YFinanceDataProvider


class FakeYFinanceModule:
    def __init__(self, ticker_cls):
        self.ticker_cls = ticker_cls
        self.requested_symbols = []

    def Ticker(self, symbol):
        self.requested_symbols.append(symbol)
        return self.ticker_cls(symbol)


class SuccessfulFakeTicker:
    def __init__(self, symbol):
        self.symbol = symbol
        self.fast_info = {"last_price": 123.45}
        self.info = {
            "longName": f"{symbol} Company",
            "sector": "Technology",
            "industry": "Semiconductors",
            "marketCap": 1000,
            "profitMargins": 0.2,
        }
        self.news = [{"title": "Company update"}]

    def history(self, **kwargs):
        dates = pd.date_range("2026-01-01", periods=60, freq="B")
        return pd.DataFrame(
            {
                "Open": range(60, 120),
                "High": range(61, 121),
                "Low": range(59, 119),
                "Close": range(60, 120),
                "Volume": [1_000_000] * 60,
            },
            index=dates,
        )


class EmptyHistoryFakeTicker:
    def __init__(self, symbol):
        self.symbol = symbol
        self.fast_info = {}
        self.info = {}
        self.news = []

    def history(self, **kwargs):
        return pd.DataFrame()


def test_yfinance_provider_uses_mocked_yfinance_history_and_latest_price():
    fake_yfinance = FakeYFinanceModule(SuccessfulFakeTicker)
    provider = YFinanceDataProvider(yf_module=fake_yfinance)

    history = provider.get_price_history("7203", MarketCode.JP)
    latest_price = provider.get_latest_price("7203", MarketCode.JP)
    status = provider.get_data_source_status()

    assert fake_yfinance.requested_symbols[0] == "7203.T"
    assert not history.empty
    assert latest_price == 119.0
    assert status["provider_name"] == "yfinance"
    assert status["quality"] == "REAL"


def test_yfinance_provider_returns_profile_metadata_from_info():
    fake_yfinance = FakeYFinanceModule(SuccessfulFakeTicker)
    provider = YFinanceDataProvider(yf_module=fake_yfinance)

    profile = provider.get_company_profile("7203", MarketCode.JP)

    assert profile["ticker"] == "7203"
    assert profile["normalized_ticker"] == "7203.T"
    assert profile["display_symbol"] == "7203.T"
    assert profile["company_name"] == "7203.T Company"


def test_yfinance_provider_fallback_to_mock_is_marked_degraded():
    fake_yfinance = FakeYFinanceModule(EmptyHistoryFakeTicker)
    provider = YFinanceDataProvider(yf_module=fake_yfinance)

    history = provider.get_price_history("NVDA", MarketCode.US)
    status = provider.get_data_source_status()

    assert not history.empty
    assert status["provider_name"] == "yfinance"
    assert status["quality"] == "DEGRADED"
    assert status["fallback_used"] is True
    assert "yfinance data unavailable; fallback mock data used." in status["warnings"]
