from abc import ABC, abstractmethod
from datetime import date

from app.core.constants import MarketCode
from app.financial_data.schemas import (
    CompanyProfile,
    DataFetchResult,
    FinancialMetricSet,
    FinancialStatementSummary,
    HistoricalPriceSeries,
    InstrumentIdentity,
    MarketQuote,
    ValuationMetricSet,
)


class FinancialDataProviderError(Exception):
    def __init__(self, message: str, *, category: str = "provider_error", retryable: bool = False) -> None:
        super().__init__(message)
        self.category = category
        self.retryable = retryable


class FinancialDataProviderAdapter(ABC):
    provider_name: str

    @abstractmethod
    def resolve_instrument(self, ticker: str, market: MarketCode) -> InstrumentIdentity:
        raise NotImplementedError

    @abstractmethod
    def get_quote(self, ticker: str, market: MarketCode) -> MarketQuote:
        raise NotImplementedError

    @abstractmethod
    def get_price_history(
        self,
        ticker: str,
        market: MarketCode,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> HistoricalPriceSeries:
        raise NotImplementedError

    @abstractmethod
    def get_company_profile(self, ticker: str, market: MarketCode) -> CompanyProfile:
        raise NotImplementedError

    @abstractmethod
    def get_financial_metrics(self, ticker: str, market: MarketCode) -> FinancialMetricSet:
        raise NotImplementedError

    @abstractmethod
    def get_financial_statements(self, ticker: str, market: MarketCode) -> FinancialStatementSummary:
        raise NotImplementedError

    @abstractmethod
    def get_valuation_metrics(self, ticker: str, market: MarketCode) -> ValuationMetricSet:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> DataFetchResult:
        raise NotImplementedError

