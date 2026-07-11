from datetime import date
import os
from typing import Callable, TypeVar

from app.core.constants import MarketCode
from app.financial_data.adapters.base import FinancialDataProviderAdapter
from app.financial_data.cache import GLOBAL_FINANCIAL_DATA_CACHE, FinancialDataCache
from app.financial_data.provider_registry import get_financial_data_adapter
from app.financial_data.schemas import (
    CompanyProfile,
    DataAvailability,
    DataFetchResult,
    DataFreshness,
    FinancialDataSnapshot,
    FinancialMetricSet,
    FinancialStatementSummary,
    HistoricalPriceSeries,
    InstrumentIdentity,
    MarketQuote,
    ValuationMetricSet,
    utc_now_iso,
)


T = TypeVar("T")


DEFAULT_TTLS = {
    "quote": 60,
    "history": 1800,
    "profile": 86400,
    "financial_metrics": 21600,
    "financial_statements": 21600,
    "valuation_metrics": 900,
    "instrument": 86400,
    "health": 300,
}


class FinancialDataService:
    def __init__(
        self,
        adapter: FinancialDataProviderAdapter | None = None,
        cache: FinancialDataCache | None = None,
        cache_enabled: bool | None = None,
    ) -> None:
        self.adapter = adapter or get_financial_data_adapter()
        self.cache = cache or GLOBAL_FINANCIAL_DATA_CACHE
        self.cache_enabled = (
            cache_enabled
            if cache_enabled is not None
            else os.getenv("FINANCIAL_DATA_CACHE_ENABLED", "true").lower() == "true"
        )

    def resolve_instrument(self, ticker: str, market: MarketCode) -> InstrumentIdentity:
        return self._cached(
            "instrument",
            (self.adapter.provider_name, ticker.upper(), market.value),
            lambda: self.adapter.resolve_instrument(ticker=ticker, market=market),
        )

    def get_quote(self, ticker: str, market: MarketCode) -> MarketQuote:
        return self._cached(
            "quote",
            (self.adapter.provider_name, ticker.upper(), market.value),
            lambda: self.adapter.get_quote(ticker=ticker, market=market),
        )

    def get_price_history(
        self,
        ticker: str,
        market: MarketCode,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> HistoricalPriceSeries:
        return self._cached(
            "history",
            (self.adapter.provider_name, ticker.upper(), market.value, str(start), str(end), interval),
            lambda: self.adapter.get_price_history(ticker=ticker, market=market, start=start, end=end, interval=interval),
        )

    def get_company_profile(self, ticker: str, market: MarketCode) -> CompanyProfile:
        return self._cached(
            "profile",
            (self.adapter.provider_name, ticker.upper(), market.value),
            lambda: self.adapter.get_company_profile(ticker=ticker, market=market),
        )

    def get_financial_metrics(self, ticker: str, market: MarketCode) -> FinancialMetricSet:
        return self._cached(
            "financial_metrics",
            (self.adapter.provider_name, ticker.upper(), market.value),
            lambda: self.adapter.get_financial_metrics(ticker=ticker, market=market),
        )

    def get_financial_statements(self, ticker: str, market: MarketCode) -> FinancialStatementSummary:
        return self._cached(
            "financial_statements",
            (self.adapter.provider_name, ticker.upper(), market.value),
            lambda: self.adapter.get_financial_statements(ticker=ticker, market=market),
        )

    def get_valuation_metrics(self, ticker: str, market: MarketCode) -> ValuationMetricSet:
        return self._cached(
            "valuation_metrics",
            (self.adapter.provider_name, ticker.upper(), market.value),
            lambda: self.adapter.get_valuation_metrics(ticker=ticker, market=market),
        )

    def health_check(self) -> DataFetchResult:
        return self._cached(
            "health",
            (self.adapter.provider_name,),
            lambda: self.adapter.health_check(),
        )

    def get_research_snapshot(self, ticker: str, market: MarketCode) -> FinancialDataSnapshot:
        instrument = self.resolve_instrument(ticker, market)
        quote = self.get_quote(ticker, market)
        history = self.get_price_history(ticker, market)
        profile = self.get_company_profile(ticker, market)
        financial_metrics = self.get_financial_metrics(ticker, market)
        financial_statements = self.get_financial_statements(ticker, market)
        valuation_metrics = self.get_valuation_metrics(ticker, market)
        components = [instrument, quote, history, profile, financial_metrics, financial_statements, valuation_metrics]
        availability = self._rollup_availability([component.availability_status for component in components])
        freshness = self._rollup_freshness([component.freshness_status for component in components if hasattr(component, "freshness_status")])
        warnings: list[str] = []
        errors: list[str] = []
        for component in components:
            warnings.extend(getattr(component, "warnings", []))
            source = getattr(component, "source", None)
            if source is not None:
                warnings.extend(source.warnings)
                errors.extend(source.errors)
        return FinancialDataSnapshot(
            instrument=instrument,
            quote=quote,
            price_history=history,
            company_profile=profile,
            financial_metrics=financial_metrics,
            financial_statements=financial_statements,
            valuation_metrics=valuation_metrics,
            provider=self.adapter.provider_name,
            availability_status=availability,
            freshness_status=freshness,
            warnings=list(dict.fromkeys(warnings)),
            errors=list(dict.fromkeys(errors)),
            fetched_at=utc_now_iso(),
        )

    def cache_status(self) -> dict[str, int | bool | str]:
        return {
            **self.cache.stats(),
            "enabled": self.cache_enabled,
            "provider": self.adapter.provider_name,
        }

    def _cached(self, data_type: str, key: tuple, fetcher: Callable[[], T]) -> T:
        cache_key = (data_type, *key)
        ttl = self._ttl(data_type)
        if self.cache_enabled:
            entry = self.cache.get(cache_key)
            if entry and entry.is_fresh:
                return entry.value
        try:
            value = fetcher()
            if self.cache_enabled:
                self.cache.set(cache_key, value, ttl)
            return value
        except Exception:
            if self.cache_enabled:
                stale_entry = self.cache.get(cache_key)
                if stale_entry is not None:
                    return self._mark_stale_cache(stale_entry.value)
            raise

    def _mark_stale_cache(self, value: T) -> T:
        if not hasattr(value, "model_copy"):
            return value
        warnings = list(getattr(value, "warnings", []))
        warnings.append("Provider refresh failed; stale cached financial data is being used.")
        updates = {
            "availability_status": DataAvailability.STALE_CACHE,
            "freshness_status": DataFreshness.STALE,
            "warnings": list(dict.fromkeys(warnings)),
        }
        return value.model_copy(update={key: val for key, val in updates.items() if hasattr(value, key)})

    def _ttl(self, data_type: str) -> int:
        env_key = f"FINANCIAL_DATA_{data_type.upper()}_TTL_SECONDS"
        try:
            return int(os.getenv(env_key, DEFAULT_TTLS[data_type]))
        except (KeyError, ValueError):
            return DEFAULT_TTLS.get(data_type, 300)

    def _rollup_availability(self, statuses: list[DataAvailability]) -> DataAvailability:
        if any(status == DataAvailability.AVAILABLE for status in statuses):
            if any(status in {DataAvailability.UNAVAILABLE, DataAvailability.FAILED, DataAvailability.UNSUPPORTED} for status in statuses):
                return DataAvailability.PARTIAL
            return DataAvailability.AVAILABLE
        if any(status == DataAvailability.STALE_CACHE for status in statuses):
            return DataAvailability.STALE_CACHE
        if any(status == DataAvailability.FAILED for status in statuses):
            return DataAvailability.FAILED
        if any(status == DataAvailability.UNSUPPORTED for status in statuses):
            return DataAvailability.UNSUPPORTED
        return DataAvailability.UNAVAILABLE

    def _rollup_freshness(self, statuses: list[DataFreshness]) -> DataFreshness:
        if any(status == DataFreshness.MATERIALLY_STALE for status in statuses):
            return DataFreshness.MATERIALLY_STALE
        if any(status == DataFreshness.STALE for status in statuses):
            return DataFreshness.STALE
        if any(status == DataFreshness.DELAYED for status in statuses):
            return DataFreshness.DELAYED
        if any(status == DataFreshness.PARTIAL for status in statuses):
            return DataFreshness.PARTIAL
        if all(status == DataFreshness.CURRENT for status in statuses):
            return DataFreshness.CURRENT
        return DataFreshness.UNKNOWN

