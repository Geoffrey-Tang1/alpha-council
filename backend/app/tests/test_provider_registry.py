from app.data_providers.mock_provider import MockDataProvider
from app.data_providers.provider_registry import get_data_provider
from app.data_providers.yfinance_provider import YFinanceDataProvider


def test_provider_registry_selects_mock(monkeypatch):
    monkeypatch.setenv("DATA_PROVIDER", "mock")

    provider = get_data_provider()

    assert isinstance(provider, MockDataProvider)


def test_provider_registry_selects_yfinance(monkeypatch):
    monkeypatch.setenv("DATA_PROVIDER", "yfinance")

    provider = get_data_provider()

    assert isinstance(provider, YFinanceDataProvider)


def test_provider_registry_unknown_falls_back_to_mock_with_warning(monkeypatch):
    monkeypatch.setenv("DATA_PROVIDER", "not_real")

    provider = get_data_provider()
    status = provider.get_data_source_status()

    assert isinstance(provider, MockDataProvider)
    assert status["quality"] == "MOCK"
    assert "Unknown DATA_PROVIDER 'not_real'; falling back to mock data." in status["warnings"]
