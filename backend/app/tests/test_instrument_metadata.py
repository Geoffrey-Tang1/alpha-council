from app.core.constants import MarketCode
from app.data_providers.mock_provider import MockDataProvider


def test_mock_provider_returns_common_company_metadata():
    provider = MockDataProvider()

    nvda = provider.get_company_profile("NVDA", MarketCode.US)
    toyota = provider.get_company_profile("7203", MarketCode.JP)
    tsmc = provider.get_company_profile("2330", MarketCode.TW)
    samsung = provider.get_company_profile("005930", MarketCode.KR)

    assert nvda["company_name"] == "NVIDIA Corporation"
    assert nvda["display_symbol"] == "NVDA"
    assert toyota["company_name"] == "Toyota Motor Corporation"
    assert toyota["normalized_ticker"] == "7203.T"
    assert tsmc["company_name"] == "Taiwan Semiconductor Manufacturing Company Limited"
    assert tsmc["display_symbol"] == "2330.TW"
    assert samsung["company_name"] == "Samsung Electronics Co., Ltd."
    assert samsung["display_symbol"] == "005930.KS"


def test_mock_provider_unknown_ticker_metadata_is_safe():
    profile = MockDataProvider().get_company_profile("ZZZZ", MarketCode.US)

    assert profile["company_name"] == "Unknown Company"
    assert profile["normalized_ticker"] == "ZZZZ"
    assert profile["display_symbol"] == "ZZZZ"
