from datetime import date
from typing import Any

import pandas as pd

from app.core.constants import MarketCode
from app.data_providers.base import MarketDataProvider
from app.data_providers.instrument_metadata import build_instrument_metadata
from app.data_providers.ticker_normalization import normalize_yfinance_ticker
from app.financial_data.adapters.base import FinancialDataProviderAdapter
from app.financial_data.freshness import (
    classify_financial_period_freshness,
    classify_history_freshness,
    classify_quote_freshness,
)
from app.financial_data.schemas import (
    CompanyProfile,
    DataAvailability,
    DataFetchResult,
    DataFreshness,
    DataSourceMetadata,
    FinancialMetric,
    FinancialMetricSet,
    FinancialPeriod,
    FinancialStatementSummary,
    HistoricalPriceBar,
    HistoricalPriceSeries,
    InstrumentIdentity,
    InstrumentType,
    MarketQuote,
    SourceType,
    ValuationMetricSet,
    utc_now_iso,
)
from app.services.market_status_service import MarketStatusService


MARKET_CURRENCY = {
    MarketCode.US: "USD",
    MarketCode.JP: "JPY",
    MarketCode.TW: "TWD",
    MarketCode.KR: "KRW",
}

MARKET_EXCHANGE = {
    MarketCode.US: "US",
    MarketCode.JP: "Tokyo Stock Exchange",
    MarketCode.TW: "Taiwan Stock Exchange",
    MarketCode.KR: "Korea Exchange",
}

KNOWN_SUFFIX_MARKETS = {
    ".T": MarketCode.JP,
    ".TW": MarketCode.TW,
    ".KS": MarketCode.KR,
}


class LegacyMarketDataFinancialAdapter(FinancialDataProviderAdapter):
    """Normalize the existing mock/yfinance provider interface.

    This adapter lets Phase 7.1 improve research traceability without changing
    the proven provider path used by backtests and decision evaluation.
    """

    def __init__(
        self,
        provider: MarketDataProvider,
        market_status_service: MarketStatusService | None = None,
    ) -> None:
        self.provider = provider
        self.provider_name = getattr(provider, "provider_name", provider.__class__.__name__.lower())
        self.market_status_service = market_status_service or MarketStatusService()

    def resolve_instrument(self, ticker: str, market: MarketCode) -> InstrumentIdentity:
        conflict = self._suffix_conflict(ticker, market)
        metadata = build_instrument_metadata(ticker=ticker, market=market)
        profile = {} if conflict else self._safe_call(lambda: self.provider.get_company_profile(ticker=ticker, market=market), {})
        display_name = profile.get("company_name") or metadata["company_name"]
        provider_symbol = metadata["normalized_ticker"]
        warnings = self._status_warnings()
        if conflict:
            warnings.append(conflict)
        source = self._source(
            provider_symbol=provider_symbol,
            observed_at=None,
            currency=MARKET_CURRENCY.get(market),
            warnings=warnings,
        )
        availability = DataAvailability.UNSUPPORTED if conflict else DataAvailability.AVAILABLE
        return InstrumentIdentity(
            instrument_id=f"{market.value}:{provider_symbol}",
            symbol=metadata["ticker"],
            display_symbol=metadata["display_symbol"],
            provider_symbol=provider_symbol,
            exchange=profile.get("exchange") or MARKET_EXCHANGE.get(market),
            market=market,
            currency=MARKET_CURRENCY.get(market),
            instrument_type=self._instrument_type(profile),
            legal_name=display_name if display_name != "Unknown Company" else None,
            display_name=display_name,
            availability_status=availability,
            confidence=0.85 if availability == DataAvailability.AVAILABLE else 0,
            warnings=warnings,
            source=source,
        )

    def get_quote(self, ticker: str, market: MarketCode) -> MarketQuote:
        instrument = self.resolve_instrument(ticker, market)
        if instrument.availability_status == DataAvailability.UNSUPPORTED:
            return MarketQuote(
                instrument_id=instrument.instrument_id,
                symbol=instrument.symbol,
                market=market,
                currency=instrument.currency,
                availability_status=DataAvailability.UNSUPPORTED,
                freshness_status=DataFreshness.UNAVAILABLE,
                confidence=0,
                source=instrument.source,
            )

        history = self.get_price_history(ticker=ticker, market=market)
        latest_price = None
        if history.bars:
            latest_price = history.bars[-1].close
        if latest_price is None:
            latest_price = self._safe_call(lambda: self.provider.get_latest_price(ticker=ticker, market=market), None)

        latest_bar = history.bars[-1] if history.bars else None
        previous_bar = history.bars[-2] if len(history.bars) >= 2 else None
        previous_close = previous_bar.close if previous_bar else None
        absolute_change = self._round_or_none(latest_price - previous_close) if latest_price is not None and previous_close else None
        percentage_change = (
            self._round_or_none((latest_price / previous_close) - 1)
            if latest_price is not None and previous_close
            else None
        )
        availability = DataAvailability.AVAILABLE if latest_price is not None else DataAvailability.UNAVAILABLE
        delayed = self.provider_name == "yfinance"
        observed_at = latest_bar.date if latest_bar else None
        source = self._source(
            provider_symbol=instrument.provider_symbol,
            observed_at=observed_at,
            currency=instrument.currency,
            delayed=delayed,
            delayed_by="Provider data may be delayed; it is not an exchange-certified real-time feed." if delayed else None,
            warnings=[*instrument.warnings, *history.warnings],
        )
        return MarketQuote(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            market=market,
            last_price=latest_price,
            previous_close=previous_close,
            open=latest_bar.open if latest_bar else None,
            day_high=latest_bar.high if latest_bar else None,
            day_low=latest_bar.low if latest_bar else None,
            volume=latest_bar.volume if latest_bar else None,
            absolute_change=absolute_change,
            percentage_change=percentage_change,
            currency=instrument.currency,
            market_status=self.market_status_service.get_market_status(market=market).status.value,
            observed_at=observed_at,
            delayed_by=source.delayed_by,
            availability_status=availability,
            freshness_status=classify_quote_freshness(observed_at, delayed=delayed, availability=availability),
            confidence=0.82 if availability == DataAvailability.AVAILABLE else 0,
            source=source,
            warnings=source.warnings,
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
        if instrument.availability_status == DataAvailability.UNSUPPORTED:
            return HistoricalPriceSeries(
                instrument_id=instrument.instrument_id,
                symbol=instrument.symbol,
                market=market,
                start_date=start,
                end_date=end,
                frequency=interval,
                availability_status=DataAvailability.UNSUPPORTED,
                freshness_status=DataFreshness.UNAVAILABLE,
                confidence=0,
                source=instrument.source,
                warnings=instrument.warnings,
            )

        raw = self._safe_call(
            lambda: self.provider.get_price_history(ticker=ticker, market=market, start=start, end=end, interval=interval),
            pd.DataFrame(),
        )
        normalized = self._normalize_history_frame(raw, currency=instrument.currency)
        availability = DataAvailability.AVAILABLE if len(normalized) >= 60 else DataAvailability.PARTIAL if len(normalized) else DataAvailability.UNAVAILABLE
        warnings = [*instrument.warnings]
        if normalized.empty:
            warnings.append("Historical daily prices are unavailable from the active provider.")
        elif len(normalized) < 60:
            warnings.append(f"Only {len(normalized)} daily price rows are available; technical evidence is partial.")
        source = self._source(
            provider_symbol=instrument.provider_symbol,
            observed_at=str(normalized.iloc[-1]["date"]) if not normalized.empty else None,
            currency=instrument.currency,
            delayed=self.provider_name == "yfinance",
            delayed_by="Daily history may be delayed or adjusted by the provider." if self.provider_name == "yfinance" else None,
            warnings=warnings,
        )
        bars = [
            HistoricalPriceBar(
                date=str(row["date"]),
                open=self._float_or_none(row.get("open")),
                high=self._float_or_none(row.get("high")),
                low=self._float_or_none(row.get("low")),
                close=self._float_or_none(row.get("close")),
                adjusted_close=self._float_or_none(row.get("adjusted_close")),
                volume=self._float_or_none(row.get("volume")),
                currency=instrument.currency,
                adjustment_status="provider_default",
            )
            for _, row in normalized.iterrows()
        ]
        return HistoricalPriceSeries(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            market=market,
            start_date=start,
            end_date=end,
            frequency=interval,
            bars=bars,
            availability_status=availability,
            freshness_status=classify_history_freshness(bars[-1].date if bars else None, availability),
            confidence=0.82 if availability == DataAvailability.AVAILABLE else 0.45 if availability == DataAvailability.PARTIAL else 0,
            source=source,
            warnings=warnings,
        )

    def get_company_profile(self, ticker: str, market: MarketCode) -> CompanyProfile:
        instrument = self.resolve_instrument(ticker, market)
        raw = {} if instrument.availability_status == DataAvailability.UNSUPPORTED else self._safe_call(
            lambda: self.provider.get_company_profile(ticker=ticker, market=market),
            {},
        )
        availability = DataAvailability.AVAILABLE if raw else instrument.availability_status
        return CompanyProfile(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            market=market,
            legal_name=raw.get("company_name") if raw.get("company_name") != "Unknown Company" else None,
            display_name=raw.get("company_name") or instrument.display_name,
            description=raw.get("description"),
            sector=raw.get("sector"),
            industry=raw.get("industry"),
            country=raw.get("country"),
            exchange=raw.get("exchange") or instrument.exchange,
            currency=instrument.currency,
            website=raw.get("website"),
            market_cap=self._float_or_none(raw.get("market_cap")),
            employee_count=self._int_or_none(raw.get("employee_count")),
            fiscal_year_end=raw.get("fiscal_year_end"),
            instrument_type=instrument.instrument_type,
            availability_status=availability,
            freshness_status=DataFreshness.UNKNOWN if availability == DataAvailability.AVAILABLE else DataFreshness.UNAVAILABLE,
            confidence=0.74 if availability == DataAvailability.AVAILABLE else 0,
            source=self._source(
                provider_symbol=instrument.provider_symbol,
                observed_at=None,
                currency=instrument.currency,
                warnings=instrument.warnings,
            ),
            warnings=instrument.warnings,
        )

    def get_financial_metrics(self, ticker: str, market: MarketCode) -> FinancialMetricSet:
        instrument = self.resolve_instrument(ticker, market)
        raw = {} if instrument.availability_status == DataAvailability.UNSUPPORTED else self._safe_call(
            lambda: self.provider.get_fundamentals(ticker=ticker, market=market),
            {},
        )
        source = self._source(
            provider_symbol=instrument.provider_symbol,
            observed_at=None,
            currency=instrument.currency,
            warnings=[*instrument.warnings, "Financial metrics are limited to fields exposed by the active provider."],
        )
        metric_specs = [
            ("revenue_growth_yoy", raw.get("revenue_growth_yoy", raw.get("revenue_growth")), None, "reported"),
            ("operating_margin", raw.get("operating_margin", raw.get("profit_margins")), None, "reported"),
            ("debt_to_equity", raw.get("debt_to_equity"), None, "reported"),
            ("free_cash_flow", raw.get("free_cash_flow"), instrument.currency, "reported"),
            ("free_cash_flow_margin", raw.get("free_cash_flow_margin"), None, "reported"),
            ("market_cap", raw.get("market_cap"), instrument.currency, "reported"),
        ]
        metrics = [
            self._metric(name, value, currency, reported_or_derived, source)
            for name, value, currency, reported_or_derived in metric_specs
            if value is not None and value != ""
        ]
        availability = DataAvailability.AVAILABLE if metrics else DataAvailability.UNAVAILABLE
        warnings = []
        if raw.get("warning"):
            warnings.append(str(raw["warning"]))
        if not metrics:
            warnings.append("No normalized financial metrics were available from the active provider.")
        return FinancialMetricSet(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            market=market,
            metrics=metrics,
            availability_status=availability,
            freshness_status=classify_financial_period_freshness(None, availability),
            confidence=0.65 if availability == DataAvailability.AVAILABLE else 0,
            source=source,
            warnings=warnings,
        )

    def get_financial_statements(self, ticker: str, market: MarketCode) -> FinancialStatementSummary:
        instrument = self.resolve_instrument(ticker, market)
        source = self._source(
            provider_symbol=instrument.provider_symbol,
            observed_at=None,
            currency=instrument.currency,
            warnings=["Full financial statements are not connected through the current provider adapter."],
        )
        return FinancialStatementSummary(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            market=market,
            availability_status=DataAvailability.UNAVAILABLE,
            freshness_status=DataFreshness.UNAVAILABLE,
            source=source,
            warnings=["Full income statement, balance sheet, and cash-flow statement history are unavailable."],
        )

    def get_valuation_metrics(self, ticker: str, market: MarketCode) -> ValuationMetricSet:
        instrument = self.resolve_instrument(ticker, market)
        raw = {} if instrument.availability_status == DataAvailability.UNSUPPORTED else self._safe_call(
            lambda: self.provider.get_fundamentals(ticker=ticker, market=market),
            {},
        )
        source = self._source(
            provider_symbol=instrument.provider_symbol,
            observed_at=None,
            currency=instrument.currency,
            warnings=[*instrument.warnings, "Valuation metrics are provider-reported unless formula is shown."],
        )
        metric_specs = [
            ("price_to_earnings", raw.get("trailing_pe"), None, "reported", None),
            ("forward_price_to_earnings", raw.get("forward_pe"), None, "reported", None),
            ("price_to_sales", raw.get("price_to_sales"), None, "reported", None),
            ("price_to_book", raw.get("price_to_book"), None, "reported", None),
            ("enterprise_value", raw.get("enterprise_value"), instrument.currency, "reported", None),
            ("enterprise_value_to_ebitda", raw.get("enterprise_value_to_ebitda"), None, "reported", None),
            ("dividend_yield", raw.get("dividend_yield"), None, "reported", None),
            ("free_cash_flow_yield", raw.get("free_cash_flow_yield"), None, "derived", "free_cash_flow / market_cap"),
            ("earnings_yield", self._earnings_yield(raw.get("trailing_pe")), None, "derived", "1 / trailing_pe"),
        ]
        metrics = [
            self._metric(name, value, currency, reported_or_derived, source, formula=formula)
            for name, value, currency, reported_or_derived, formula in metric_specs
            if value is not None and value != ""
        ]
        availability = DataAvailability.AVAILABLE if metrics else DataAvailability.UNAVAILABLE
        warnings = [] if metrics else ["No normalized valuation metrics were available from the active provider."]
        return ValuationMetricSet(
            instrument_id=instrument.instrument_id,
            symbol=instrument.symbol,
            market=market,
            metrics=metrics,
            availability_status=availability,
            freshness_status=classify_financial_period_freshness(None, availability),
            confidence=0.62 if availability == DataAvailability.AVAILABLE else 0,
            source=source,
            warnings=warnings,
        )

    def health_check(self) -> DataFetchResult:
        status = self.provider.get_data_source_status()
        availability = DataAvailability.AVAILABLE if status.get("status") in {"OK", "UNKNOWN"} else DataAvailability.PARTIAL
        source = self._source(
            provider_symbol=status.get("normalized_ticker"),
            observed_at=None,
            currency=None,
            warnings=status.get("warnings", []),
        )
        return DataFetchResult(
            data_type="provider_status",
            availability_status=availability,
            freshness_status=DataFreshness.CURRENT if availability == DataAvailability.AVAILABLE else DataFreshness.UNKNOWN,
            source=source,
            payload={
                "provider": self.provider_name,
                "status": status.get("status", "UNKNOWN"),
                "quality": status.get("quality", "UNAVAILABLE"),
                "capabilities": [
                    "instrument_resolution",
                    "quote",
                    "daily_price_history",
                    "company_profile",
                    "basic_financial_metrics",
                    "basic_valuation_metrics",
                ],
            },
            warnings=status.get("warnings", []),
        )

    def _normalize_history_frame(self, history: pd.DataFrame, currency: str | None) -> pd.DataFrame:
        if history is None or history.empty:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "adjusted_close", "volume", "currency"])
        frame = history.copy()
        column_map = {
            "Date": "date",
            "Datetime": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adjusted_close",
            "Volume": "volume",
        }
        frame = frame.reset_index().rename(columns=column_map)
        if "index" in frame and "date" not in frame:
            frame = frame.rename(columns={"index": "date"})
        for column in ["date", "open", "high", "low", "close", "adjusted_close", "volume"]:
            if column not in frame:
                frame[column] = None
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.date.astype(str)
        for column in ["open", "high", "low", "close", "adjusted_close", "volume"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame[frame["date"] != "NaT"].dropna(subset=["close"])
        frame = frame.sort_values("date").drop_duplicates(subset=["date"], keep="last")
        frame["currency"] = currency
        return frame[["date", "open", "high", "low", "close", "adjusted_close", "volume", "currency"]].reset_index(drop=True)

    def _metric(
        self,
        name: str,
        value: Any,
        currency: str | None,
        reported_or_derived: str,
        source: DataSourceMetadata,
        formula: str | None = None,
    ) -> FinancialMetric:
        return FinancialMetric(
            name=name,
            value=self._float_or_original(value),
            currency=currency,
            reported_or_derived=reported_or_derived,
            formula=formula,
            source=source.model_copy(update={
                "transformation_type": "derived_calculation" if reported_or_derived == "derived" else "provider_normalization",
                "is_derived": reported_or_derived == "derived",
                "formula": formula,
            }),
        )

    def _source(
        self,
        provider_symbol: str | None,
        observed_at: str | None,
        currency: str | None,
        warnings: list[str],
        *,
        delayed: bool = False,
        delayed_by: str | None = None,
    ) -> DataSourceMetadata:
        return DataSourceMetadata(
            provider=self.provider_name,
            provider_symbol=provider_symbol,
            source_type=SourceType.MOCK_DATA if self.provider_name == "mock" else SourceType.MARKET_DATA_PROVIDER,
            fetched_at=utc_now_iso(),
            observed_at=observed_at,
            currency=currency,
            delayed=delayed,
            delayed_by=delayed_by,
            transformation_type="provider_normalization",
            warnings=list(dict.fromkeys(warnings)),
        )

    def _status_warnings(self) -> list[str]:
        try:
            return list(self.provider.get_data_source_status().get("warnings", []))
        except Exception:
            return ["Provider status is unavailable."]

    def _suffix_conflict(self, ticker: str, market: MarketCode) -> str | None:
        clean = ticker.strip().upper()
        for suffix, suffix_market in KNOWN_SUFFIX_MARKETS.items():
            if clean.endswith(suffix) and suffix_market != market:
                return f"Ticker suffix {suffix} conflicts with selected market {market.value}; instrument is unsupported until corrected."
        return None

    def _instrument_type(self, profile: dict) -> InstrumentType:
        quote_type = str(profile.get("quote_type") or profile.get("instrument_type") or "").lower()
        if "etf" in quote_type:
            return InstrumentType.ETF
        if quote_type in {"equity", "stock"} or profile:
            return InstrumentType.EQUITY
        return InstrumentType.UNKNOWN

    def _safe_call(self, fn, default):
        try:
            return fn()
        except Exception:
            return default

    def _round_or_none(self, value: float | None) -> float | None:
        return round(float(value), 6) if value is not None else None

    def _float_or_none(self, value) -> float | None:
        try:
            if pd.isna(value):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _float_or_original(self, value):
        as_float = self._float_or_none(value)
        return as_float if as_float is not None else value

    def _int_or_none(self, value) -> int | None:
        try:
            if value is None or pd.isna(value):
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    def _earnings_yield(self, trailing_pe) -> float | None:
        pe = self._float_or_none(trailing_pe)
        if pe is None or pe == 0:
            return None
        return round(1 / pe, 6)
