from datetime import date

from app.core.constants import MarketCode
from app.data_providers.instrument_metadata import build_instrument_metadata
from app.financial_data.adapters.base import FinancialDataProviderAdapter
from app.financial_data.schemas import (
    CompanyProfile,
    DataAvailability,
    DataFetchResult,
    DataFreshness,
    DataSourceMetadata,
    FinancialMetricSet,
    FinancialStatementSummary,
    HistoricalPriceSeries,
    InstrumentIdentity,
    InstrumentType,
    MarketQuote,
    SourceType,
    ValuationMetricSet,
    utc_now_iso,
)


class DisabledFinancialDataAdapter(FinancialDataProviderAdapter):
    provider_name = "disabled"

    def resolve_instrument(self, ticker: str, market: MarketCode) -> InstrumentIdentity:
        metadata = build_instrument_metadata(ticker=ticker, market=market)
        source = self._source(metadata["normalized_ticker"], ["Financial data provider is disabled."])
        return InstrumentIdentity(
            instrument_id=f"{market.value}:{metadata['normalized_ticker']}",
            symbol=metadata["ticker"],
            display_symbol=metadata["display_symbol"],
            provider_symbol=metadata["normalized_ticker"],
            market=market,
            instrument_type=InstrumentType.UNKNOWN,
            display_name=metadata["company_name"],
            availability_status=DataAvailability.UNAVAILABLE,
            confidence=0,
            warnings=["Financial data provider is disabled."],
            source=source,
        )

    def get_quote(self, ticker: str, market: MarketCode) -> MarketQuote:
        instrument = self.resolve_instrument(ticker, market)
        return MarketQuote(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            market=market,
            availability_status=DataAvailability.UNAVAILABLE,
            freshness_status=DataFreshness.UNAVAILABLE,
            confidence=0,
            source=instrument.source,
            warnings=["Financial data provider is disabled."],
        )

    def get_price_history(
        self,
        ticker: str,
        market: MarketCode,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> HistoricalPriceSeries:
        instrument = self.resolve_instrument(ticker, market)
        return HistoricalPriceSeries(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            market=market,
            start_date=start,
            end_date=end,
            frequency=interval,
            availability_status=DataAvailability.UNAVAILABLE,
            freshness_status=DataFreshness.UNAVAILABLE,
            confidence=0,
            source=instrument.source,
            warnings=["Financial data provider is disabled."],
        )

    def get_company_profile(self, ticker: str, market: MarketCode) -> CompanyProfile:
        instrument = self.resolve_instrument(ticker, market)
        return CompanyProfile(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            market=market,
            display_name=instrument.display_name,
            availability_status=DataAvailability.UNAVAILABLE,
            freshness_status=DataFreshness.UNAVAILABLE,
            confidence=0,
            source=instrument.source,
            warnings=["Financial data provider is disabled."],
        )

    def get_financial_metrics(self, ticker: str, market: MarketCode) -> FinancialMetricSet:
        instrument = self.resolve_instrument(ticker, market)
        return FinancialMetricSet(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            market=market,
            availability_status=DataAvailability.UNAVAILABLE,
            freshness_status=DataFreshness.UNAVAILABLE,
            confidence=0,
            source=instrument.source,
            warnings=["Financial metrics unavailable because financial data provider is disabled."],
        )

    def get_financial_statements(self, ticker: str, market: MarketCode) -> FinancialStatementSummary:
        instrument = self.resolve_instrument(ticker, market)
        return FinancialStatementSummary(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            market=market,
            availability_status=DataAvailability.UNAVAILABLE,
            freshness_status=DataFreshness.UNAVAILABLE,
            source=instrument.source,
            warnings=["Financial statements unavailable because financial data provider is disabled."],
        )

    def get_valuation_metrics(self, ticker: str, market: MarketCode) -> ValuationMetricSet:
        instrument = self.resolve_instrument(ticker, market)
        return ValuationMetricSet(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            market=market,
            availability_status=DataAvailability.UNAVAILABLE,
            freshness_status=DataFreshness.UNAVAILABLE,
            confidence=0,
            source=instrument.source,
            warnings=["Valuation metrics unavailable because financial data provider is disabled."],
        )

    def health_check(self) -> DataFetchResult:
        source = self._source(None, ["Financial data provider is disabled."])
        return DataFetchResult(
            data_type="provider_status",
            availability_status=DataAvailability.UNAVAILABLE,
            freshness_status=DataFreshness.UNAVAILABLE,
            source=source,
            warnings=["Financial data provider is disabled."],
        )

    def _source(self, provider_symbol: str | None, warnings: list[str]) -> DataSourceMetadata:
        return DataSourceMetadata(
            provider=self.provider_name,
            provider_symbol=provider_symbol,
            source_type=SourceType.UNAVAILABLE_SOURCE,
            fetched_at=utc_now_iso(),
            warnings=warnings,
        )
