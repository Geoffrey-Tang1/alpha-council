from datetime import date, datetime, timedelta, timezone

import pandas as pd

from app.core.constants import MarketCode
from app.data_providers.base import MarketDataProvider
from app.data_providers.mock_provider import MockDataProvider
from app.financial_data.adapters.base import FinancialDataProviderAdapter
from app.financial_data.adapters.disabled import DisabledFinancialDataAdapter
from app.financial_data.adapters.legacy_market_data import LegacyMarketDataFinancialAdapter
from app.financial_data.cache import FinancialDataCache
from app.financial_data.schemas import (
    DataAvailability,
    DataFreshness,
    DataSourceMetadata,
    FinancialMetricSet,
    HistoricalPriceSeries,
    InstrumentIdentity,
    MarketQuote,
    SourceType,
    utc_now_iso,
)
from app.schemas.analysis import AnalysisRequest
from app.services import analysis_service as analysis_module
from app.services.analysis_service import AnalysisService
from app.services.financial_data_service import FinancialDataService


class DuplicateHistoryProvider(MockDataProvider):
    def get_price_history(
        self,
        ticker: str,
        market: MarketCode,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"date": "2026-01-03", "open": 12, "high": 13, "low": 11, "close": 12, "volume": 100},
                {"date": "2026-01-02", "open": 10, "high": 11, "low": 9, "close": 10, "volume": 100},
                {"date": "2026-01-02", "open": 11, "high": 12, "low": 10, "close": 11, "volume": 200},
            ]
        )


class UnsafeProfileProvider(MockDataProvider):
    def __init__(self, profile_overrides: dict) -> None:
        super().__init__()
        self.profile_overrides = profile_overrides

    def get_company_profile(self, ticker: str, market: MarketCode) -> dict:
        profile = super().get_company_profile(ticker=ticker, market=market)
        profile.update(self.profile_overrides)
        return profile


class CountingQuoteAdapter(FinancialDataProviderAdapter):
    provider_name = "counting"

    def __init__(self) -> None:
        self.quote_calls = 0
        self.fail = False

    def resolve_instrument(self, ticker: str, market: MarketCode) -> InstrumentIdentity:
        source = self._source(ticker)
        return InstrumentIdentity(
            instrument_id=f"{market.value}:{ticker}",
            symbol=ticker,
            display_symbol=ticker,
            provider_symbol=ticker,
            market=market,
            currency="USD",
            display_name="Counting Company",
            availability_status=DataAvailability.AVAILABLE,
            source=source,
        )

    def get_quote(self, ticker: str, market: MarketCode) -> MarketQuote:
        self.quote_calls += 1
        if self.fail:
            raise RuntimeError("temporary provider failure")
        instrument = self.resolve_instrument(ticker, market)
        return MarketQuote(
            instrument_id=instrument.instrument_id,
            symbol=ticker,
            market=market,
            last_price=100 + self.quote_calls,
            currency="USD",
            availability_status=DataAvailability.AVAILABLE,
            freshness_status=DataFreshness.CURRENT,
            source=instrument.source,
        )

    def get_price_history(self, ticker, market, start=None, end=None, interval="1d") -> HistoricalPriceSeries:
        raise NotImplementedError

    def get_company_profile(self, ticker, market):
        raise NotImplementedError

    def get_financial_metrics(self, ticker, market) -> FinancialMetricSet:
        raise NotImplementedError

    def get_financial_statements(self, ticker, market):
        raise NotImplementedError

    def get_valuation_metrics(self, ticker, market):
        raise NotImplementedError

    def health_check(self):
        raise NotImplementedError

    def _source(self, ticker: str) -> DataSourceMetadata:
        return DataSourceMetadata(
            provider=self.provider_name,
            provider_symbol=ticker,
            source_type=SourceType.MARKET_DATA_PROVIDER,
            fetched_at=utc_now_iso(),
        )


def test_legacy_adapter_resolves_instrument_and_quote_with_provenance():
    adapter = LegacyMarketDataFinancialAdapter(MockDataProvider())

    identity = adapter.resolve_instrument("NVDA", MarketCode.US)
    quote = adapter.get_quote("NVDA", MarketCode.US)

    assert identity.display_name == "NVIDIA Corporation"
    assert identity.provider_symbol == "NVDA"
    assert quote.last_price is not None
    assert quote.source.provider == "mock"
    assert quote.source.provider_symbol == "NVDA"
    assert quote.availability_status == DataAvailability.AVAILABLE


def test_suffix_conflict_is_marked_unsupported():
    adapter = LegacyMarketDataFinancialAdapter(MockDataProvider())

    identity = adapter.resolve_instrument("2330.TW", MarketCode.JP)

    assert identity.availability_status == DataAvailability.UNSUPPORTED
    assert any("conflicts" in warning for warning in identity.warnings)


def test_history_normalization_sorts_and_removes_duplicate_dates():
    adapter = LegacyMarketDataFinancialAdapter(DuplicateHistoryProvider())

    history = adapter.get_price_history("NVDA", MarketCode.US)

    assert [bar.date for bar in history.bars] == ["2026-01-02", "2026-01-03"]
    assert history.bars[0].close == 11
    assert history.warnings


def test_financial_and_valuation_metrics_are_normalized():
    adapter = LegacyMarketDataFinancialAdapter(MockDataProvider())

    financial_metrics = adapter.get_financial_metrics("NVDA", MarketCode.US)
    valuation_metrics = adapter.get_valuation_metrics("NVDA", MarketCode.US)

    assert "revenue_growth_yoy" in financial_metrics.by_name()
    assert "price_to_earnings" in valuation_metrics.by_name()
    earnings_yield = next(metric for metric in valuation_metrics.metrics if metric.name == "earnings_yield")
    assert earnings_yield.reported_or_derived == "derived"
    assert earnings_yield.formula == "1 / trailing_pe"


def test_company_profile_normalizes_fiscal_year_end_timestamp():
    adapter = LegacyMarketDataFinancialAdapter(
        UnsafeProfileProvider({"fiscal_year_end": 1769299200})
    )

    profile = adapter.get_company_profile("NVDA", MarketCode.US)

    assert profile.fiscal_year_end == "2026-01-25"
    assert any("fiscal_year_end timestamp was normalized" in warning for warning in profile.warnings)


def test_company_profile_keeps_fiscal_year_end_string():
    adapter = LegacyMarketDataFinancialAdapter(
        UnsafeProfileProvider({"fiscal_year_end": "2026-01-25"})
    )

    profile = adapter.get_company_profile("NVDA", MarketCode.US)

    assert profile.fiscal_year_end == "2026-01-25"
    assert not any("fiscal_year_end" in warning for warning in profile.warnings)


def test_company_profile_omits_invalid_fiscal_year_end_with_warning():
    adapter = LegacyMarketDataFinancialAdapter(
        UnsafeProfileProvider({"fiscal_year_end": ["2026-01-25"]})
    )

    profile = adapter.get_company_profile("NVDA", MarketCode.US)

    assert profile.fiscal_year_end is None
    assert any("fiscal_year_end had unsupported type list" in warning for warning in profile.warnings)


def test_company_profile_malformed_fields_return_warnings_not_validation_errors():
    adapter = LegacyMarketDataFinancialAdapter(
        UnsafeProfileProvider(
            {
                "sector": ["Technology"],
                "industry": {"name": "Semiconductors"},
                "country": 123,
                "exchange": ["NASDAQ"],
                "website": {"url": "https://example.invalid"},
                "currency": ["USD"],
                "market_cap": ["large"],
                "employee_count": {"count": 1},
                "fiscal_year_end": object(),
            }
        )
    )

    profile = adapter.get_company_profile("NVDA", MarketCode.US)

    assert profile.sector is None
    assert profile.industry is None
    assert profile.country == "123"
    assert profile.exchange == "US"
    assert profile.website is None
    assert profile.currency == "USD"
    assert profile.market_cap is None
    assert profile.employee_count is None
    assert profile.fiscal_year_end is None
    assert len(profile.warnings) >= 6


def test_disabled_financial_provider_returns_unavailable_state():
    adapter = DisabledFinancialDataAdapter()

    quote = adapter.get_quote("NVDA", MarketCode.US)
    health = adapter.health_check()

    assert quote.availability_status == DataAvailability.UNAVAILABLE
    assert health.availability_status == DataAvailability.UNAVAILABLE
    assert health.source.provider == "disabled"


def test_financial_data_service_cache_hit_avoids_second_provider_call():
    adapter = CountingQuoteAdapter()
    service = FinancialDataService(adapter=adapter, cache=FinancialDataCache())

    first = service.get_quote("NVDA", MarketCode.US)
    second = service.get_quote("NVDA", MarketCode.US)

    assert first.last_price == second.last_price
    assert adapter.quote_calls == 1


def test_financial_data_service_uses_stale_cache_on_refresh_failure():
    adapter = CountingQuoteAdapter()
    cache = FinancialDataCache()
    service = FinancialDataService(adapter=adapter, cache=cache)

    first = service.get_quote("NVDA", MarketCode.US)
    cache_key = ("quote", adapter.provider_name, "NVDA", MarketCode.US.value)
    cache.get(cache_key).cached_at = datetime.now(timezone.utc) - timedelta(days=1)
    adapter.fail = True

    fallback = service.get_quote("NVDA", MarketCode.US)

    assert first.last_price == fallback.last_price
    assert fallback.availability_status == DataAvailability.STALE_CACHE
    assert fallback.freshness_status == DataFreshness.STALE
    assert any("stale cached" in warning for warning in fallback.warnings)


def test_financial_data_api_returns_provider_neutral_quote(client):
    response = client.get("/api/v1/financial-data/quote?ticker=NVDA&market=US")

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "NVDA"
    assert body["source"]["provider"] == "mock"
    assert body["source"]["provider_symbol"] == "NVDA"
    assert body["availability_status"] == "available"


def test_financial_data_snapshot_api_returns_snapshot(client):
    response = client.get("/api/v1/financial-data/snapshot?ticker=NVDA&market=US")

    assert response.status_code == 200
    body = response.json()
    assert body["instrument"]["provider_symbol"] == "NVDA"
    assert body["company_profile"]["display_name"] == "NVIDIA Corporation"
    assert body["quote"]["availability_status"] == "available"


def test_financial_snapshot_with_malformed_profile_fields_returns_warnings():
    provider = UnsafeProfileProvider(
        {
            "fiscal_year_end": ["bad"],
            "sector": ["Technology"],
            "market_cap": {"value": 1},
        }
    )
    service = FinancialDataService(
        adapter=LegacyMarketDataFinancialAdapter(provider),
        cache=FinancialDataCache(),
    )

    snapshot = service.get_research_snapshot("NVDA", MarketCode.US)

    assert snapshot.company_profile.fiscal_year_end is None
    assert snapshot.company_profile.sector is None
    assert any("fiscal_year_end had unsupported type list" in warning for warning in snapshot.warnings)
    assert any("sector had unsupported type list" in warning for warning in snapshot.warnings)


def test_financial_data_status_is_safe_for_frontend(client):
    response = client.get("/api/v1/financial-data/status")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["configuration"]["api_key_returned_to_frontend"] is False
    assert "quote" in body["capabilities"]


def test_research_report_includes_financial_data_provenance(client):
    response = client.post(
        "/api/v1/analysis/run",
        json={
            "ticker": "NVDA",
            "market": "US",
            "time_horizon": "swing",
            "strategy_preference": "moving_average_crossover",
        },
    )

    assert response.status_code == 200
    evidence = response.json()["research_report"]["evidence"]
    latest_price = next(item for item in evidence if item["evidence_id"] == "ev_latest_price")
    valuation = [item for item in evidence if item["category"] == "valuation"]
    statements = next(item for item in evidence if item["evidence_id"] == "ev_financial_statements_unavailable")

    assert latest_price["provider_symbol"] == "NVDA"
    assert latest_price["fetched_at"]
    assert latest_price["source_type"] == "mock_data"
    assert valuation
    assert statements["availability_status"] == "unavailable"
    assert statements["source_reference"] is None


def test_analysis_with_malformed_provider_profile_does_not_crash(monkeypatch):
    provider = UnsafeProfileProvider(
        {
            "fiscal_year_end": 1769299200,
            "sector": ["Technology"],
            "market_cap": ["large"],
        }
    )
    monkeypatch.setattr(analysis_module, "get_data_provider", lambda: provider)
    service = AnalysisService()

    decision = service.run_analysis(
        AnalysisRequest(
            ticker="NVDA",
            market=MarketCode.US,
            time_horizon="swing",
            strategy_preference="moving_average_crossover",
        )
    )

    assert decision.research_report is not None
    assert any(
        "fiscal_year_end timestamp was normalized" in warning
        for item in decision.research_report.evidence
        for warning in item.warnings
    )
