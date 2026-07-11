from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from app.core.constants import MarketCode


FINANCIAL_DATA_SCHEMA_VERSION = "financial_data_v1"


class DataAvailability(StrEnum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
    STALE_CACHE = "stale_cache"


class DataFreshness(StrEnum):
    CURRENT = "current"
    DELAYED = "delayed"
    STALE = "stale"
    MATERIALLY_STALE = "materially_stale"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"


class InstrumentType(StrEnum):
    EQUITY = "equity"
    ETF = "etf"
    UNKNOWN = "unknown"


class SourceType(StrEnum):
    MARKET_DATA_PROVIDER = "market_data_provider"
    INTERNAL_CALCULATION = "internal_calculation"
    MOCK_DATA = "mock_data"
    UNAVAILABLE_SOURCE = "unavailable_source"


class DataSourceMetadata(BaseModel):
    provider: str
    provider_symbol: str | None = None
    source_type: SourceType
    source_reference: str | None = None
    fetched_at: str
    observed_at: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    currency: str | None = None
    delayed: bool = False
    delayed_by: str | None = None
    transformation_type: str = "original"
    is_derived: bool = False
    formula: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class InstrumentIdentity(BaseModel):
    instrument_id: str
    symbol: str
    display_symbol: str
    provider_symbol: str
    exchange: str | None = None
    market: MarketCode
    currency: str | None = None
    instrument_type: InstrumentType = InstrumentType.UNKNOWN
    legal_name: str | None = None
    display_name: str = "Unknown Company"
    availability_status: DataAvailability
    confidence: float = Field(ge=0, le=1, default=0.5)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    source: DataSourceMetadata


class MarketQuote(BaseModel):
    instrument_id: str
    symbol: str
    market: MarketCode
    last_price: float | None = None
    previous_close: float | None = None
    open: float | None = None
    day_high: float | None = None
    day_low: float | None = None
    volume: float | None = None
    absolute_change: float | None = None
    percentage_change: float | None = None
    currency: str | None = None
    market_status: str | None = None
    observed_at: str | None = None
    delayed_by: str | None = None
    availability_status: DataAvailability
    freshness_status: DataFreshness
    confidence: float = Field(ge=0, le=1, default=0.5)
    source: DataSourceMetadata
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class HistoricalPriceBar(BaseModel):
    date: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    adjusted_close: float | None = None
    volume: float | None = None
    currency: str | None = None
    adjustment_status: str = "provider_default"


class HistoricalPriceSeries(BaseModel):
    instrument_id: str
    symbol: str
    market: MarketCode
    start_date: date | None = None
    end_date: date | None = None
    frequency: str = "1d"
    bars: list[HistoricalPriceBar] = Field(default_factory=list)
    availability_status: DataAvailability
    freshness_status: DataFreshness
    confidence: float = Field(ge=0, le=1, default=0.5)
    source: DataSourceMetadata
    warnings: list[str] = Field(default_factory=list)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([bar.model_dump() for bar in self.bars])


class CompanyProfile(BaseModel):
    instrument_id: str
    symbol: str
    market: MarketCode
    legal_name: str | None = None
    display_name: str = "Unknown Company"
    description: str | None = None
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    exchange: str | None = None
    currency: str | None = None
    website: str | None = None
    market_cap: float | None = None
    employee_count: int | None = None
    fiscal_year_end: str | None = None
    instrument_type: InstrumentType = InstrumentType.UNKNOWN
    availability_status: DataAvailability
    freshness_status: DataFreshness
    confidence: float = Field(ge=0, le=1, default=0.5)
    source: DataSourceMetadata
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class FinancialPeriod(BaseModel):
    period_start: str | None = None
    period_end: str | None = None
    frequency: str = "unknown"
    fiscal_year: int | None = None
    fiscal_period: str | None = None


class FinancialMetric(BaseModel):
    name: str
    value: float | int | str | None
    currency: str | None = None
    period: FinancialPeriod = Field(default_factory=FinancialPeriod)
    reported_or_derived: str = "reported"
    formula: str | None = None
    availability_status: DataAvailability = DataAvailability.AVAILABLE
    source: DataSourceMetadata
    warnings: list[str] = Field(default_factory=list)


class FinancialStatementSummary(BaseModel):
    instrument_id: str
    symbol: str
    market: MarketCode
    period: FinancialPeriod = Field(default_factory=FinancialPeriod)
    metrics: list[FinancialMetric] = Field(default_factory=list)
    availability_status: DataAvailability
    freshness_status: DataFreshness
    source: DataSourceMetadata
    warnings: list[str] = Field(default_factory=list)


class FinancialMetricSet(BaseModel):
    instrument_id: str
    symbol: str
    market: MarketCode
    metrics: list[FinancialMetric] = Field(default_factory=list)
    availability_status: DataAvailability
    freshness_status: DataFreshness
    confidence: float = Field(ge=0, le=1, default=0.5)
    source: DataSourceMetadata
    warnings: list[str] = Field(default_factory=list)

    def by_name(self) -> dict[str, float | int | str | None]:
        return {metric.name: metric.value for metric in self.metrics}


class ValuationMetricSet(BaseModel):
    instrument_id: str
    symbol: str
    market: MarketCode
    metrics: list[FinancialMetric] = Field(default_factory=list)
    availability_status: DataAvailability
    freshness_status: DataFreshness
    confidence: float = Field(ge=0, le=1, default=0.5)
    source: DataSourceMetadata
    warnings: list[str] = Field(default_factory=list)

    def by_name(self) -> dict[str, float | int | str | None]:
        return {metric.name: metric.value for metric in self.metrics}


class DataFetchResult(BaseModel):
    data_type: str
    availability_status: DataAvailability
    freshness_status: DataFreshness
    source: DataSourceMetadata
    payload: dict[str, Any] | list[dict[str, Any]] | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class FinancialDataSnapshot(BaseModel):
    schema_version: str = FINANCIAL_DATA_SCHEMA_VERSION
    instrument: InstrumentIdentity
    quote: MarketQuote
    price_history: HistoricalPriceSeries
    company_profile: CompanyProfile
    financial_metrics: FinancialMetricSet
    financial_statements: FinancialStatementSummary
    valuation_metrics: ValuationMetricSet
    provider: str
    availability_status: DataAvailability
    freshness_status: DataFreshness
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    fetched_at: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
