from datetime import date
from typing import Any

import pandas as pd
import yfinance as yf

from app.core.constants import MarketCode
from app.data_providers.base import MarketDataProvider
from app.data_providers.mock_provider import MockDataProvider
from app.data_providers.ticker_normalization import normalize_yfinance_ticker


class YFinanceDataProvider(MarketDataProvider):
    """Optional real-data provider backed by yfinance.

    yfinance is useful for local research, but it is not an exchange feed and
    may be delayed, incomplete, adjusted, throttled, or unavailable.
    """

    provider_name = "yfinance"

    def __init__(
        self,
        yf_module: Any = yf,
        fallback_provider: MarketDataProvider | None = None,
    ) -> None:
        self.yf = yf_module
        self.fallback_provider = fallback_provider or MockDataProvider()
        self._last_status = self._status(
            quality="UNAVAILABLE",
            status="UNKNOWN",
            warnings=["No yfinance request has completed yet."],
        )
        self._history_cache: dict[tuple[str, MarketCode], pd.DataFrame] = {}

    def get_price_history(
        self,
        ticker: str,
        market: MarketCode,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        normalized_ticker = normalize_yfinance_ticker(ticker=ticker, market=market)
        cache_key = (normalized_ticker, market)
        try:
            yfinance_ticker = self.yf.Ticker(normalized_ticker)
            history_kwargs: dict[str, Any] = {
                "interval": interval,
                "auto_adjust": False,
            }
            if start or end:
                if start:
                    history_kwargs["start"] = start.isoformat()
                if end:
                    history_kwargs["end"] = end.isoformat()
            else:
                history_kwargs["period"] = "6mo"

            raw_history = yfinance_ticker.history(**history_kwargs)
            normalized_history = self._normalize_history(raw_history)
            if normalized_history.empty:
                return self._fallback_history(
                    ticker=ticker,
                    market=market,
                    warning=f"yfinance returned no price history for {normalized_ticker}; fallback mock data used.",
                )

            if len(normalized_history) < 50:
                self._last_status = self._status(
                    quality="DEGRADED",
                    status="DEGRADED",
                    normalized_ticker=normalized_ticker,
                    warnings=[
                        f"yfinance returned only {len(normalized_history)} rows for {normalized_ticker}; technical analysis may be limited."
                    ],
                )
            else:
                self._last_status = self._status(
                    quality="REAL",
                    status="OK",
                    normalized_ticker=normalized_ticker,
                    warnings=[
                        "Market data provided by yfinance. Data may be delayed, incomplete, or adjusted."
                    ],
                )

            self._history_cache[cache_key] = normalized_history
            return normalized_history
        except Exception as exc:  # pragma: no cover - exact yfinance errors vary
            return self._fallback_history(
                ticker=ticker,
                market=market,
                warning=f"yfinance price history failed for {normalized_ticker}: {exc}; fallback mock data used.",
            )

    def get_latest_price(self, ticker: str, market: MarketCode) -> float | None:
        normalized_ticker = normalize_yfinance_ticker(ticker=ticker, market=market)
        cache_key = (normalized_ticker, market)
        cached_history = self._history_cache.get(cache_key)
        if cached_history is not None and not cached_history.empty:
            return float(cached_history.iloc[-1]["close"])

        try:
            yfinance_ticker = self.yf.Ticker(normalized_ticker)
            fast_info = getattr(yfinance_ticker, "fast_info", {}) or {}
            latest_price = self._read_fast_info_price(fast_info)
            if latest_price is not None:
                return latest_price

            history = self.get_price_history(ticker=ticker, market=market)
            if history.empty:
                self._last_status = self._status(
                    quality="UNAVAILABLE",
                    status="DOWN",
                    normalized_ticker=normalized_ticker,
                    warnings=[f"yfinance latest price unavailable for {normalized_ticker}."],
                )
                return None
            return float(history.iloc[-1]["close"])
        except Exception as exc:  # pragma: no cover - exact yfinance errors vary
            fallback_price = self.fallback_provider.get_latest_price(ticker=ticker, market=market)
            self._last_status = self._status(
                quality="DEGRADED" if fallback_price is not None else "UNAVAILABLE",
                status="DEGRADED" if fallback_price is not None else "DOWN",
                normalized_ticker=normalized_ticker,
                fallback_used=fallback_price is not None,
                warnings=[f"yfinance latest price failed for {normalized_ticker}: {exc}; fallback mock data used."],
            )
            return fallback_price

    def get_company_profile(self, ticker: str, market: MarketCode) -> dict:
        normalized_ticker = normalize_yfinance_ticker(ticker=ticker, market=market)
        try:
            info = self.yf.Ticker(normalized_ticker).info or {}
            return {
                "ticker": normalized_ticker,
                "market": market.value,
                "company_name": info.get("longName") or info.get("shortName") or normalized_ticker,
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "exchange": info.get("exchange"),
                "is_mock": False,
            }
        except Exception as exc:  # pragma: no cover - exact yfinance errors vary
            self._append_warning(f"yfinance company profile unavailable for {normalized_ticker}: {exc}.")
            return {
                "ticker": normalized_ticker,
                "market": market.value,
                "company_name": normalized_ticker,
                "sector": None,
                "industry": None,
                "exchange": None,
                "is_mock": False,
            }

    def get_fundamentals(self, ticker: str, market: MarketCode) -> dict:
        normalized_ticker = normalize_yfinance_ticker(ticker=ticker, market=market)
        try:
            info = self.yf.Ticker(normalized_ticker).info or {}
            return {
                "market_cap": info.get("marketCap"),
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "profit_margins": info.get("profitMargins"),
                "debt_to_equity": info.get("debtToEquity"),
                "revenue_growth": info.get("revenueGrowth"),
                "free_cash_flow": info.get("freeCashflow"),
                "is_mock": False,
            }
        except Exception as exc:  # pragma: no cover - exact yfinance errors vary
            self._append_warning(f"yfinance fundamentals unavailable for {normalized_ticker}: {exc}.")
            return {
                "is_mock": False,
                "warning": "Fundamental data unavailable from yfinance.",
            }

    def get_news(self, ticker: str, market: MarketCode, limit: int = 5) -> list[dict]:
        normalized_ticker = normalize_yfinance_ticker(ticker=ticker, market=market)
        try:
            raw_news = getattr(self.yf.Ticker(normalized_ticker), "news", []) or []
            news_items = []
            for item in raw_news[:limit]:
                content = item.get("content", item) if isinstance(item, dict) else {}
                news_items.append(
                    {
                        "headline": content.get("title") or item.get("title") or "Untitled yfinance news item",
                        "source": "yfinance",
                        "sentiment": "unknown",
                        "is_mock": False,
                    }
                )
            if news_items:
                return news_items
        except Exception as exc:  # pragma: no cover - exact yfinance errors vary
            self._append_warning(f"yfinance news unavailable for {normalized_ticker}: {exc}.")

        return [
            {
                "headline": f"{normalized_ticker}: yfinance news unavailable or not configured for this symbol.",
                "source": "yfinance_placeholder",
                "sentiment": "unknown",
                "is_mock": False,
            }
        ]

    def get_macro_context(self, market: MarketCode) -> dict:
        return {
            "risk_environment": "unknown",
            "summary": "Macro context remains placeholder logic in Phase 3; yfinance is used for symbol-level market data only.",
            "is_mock": False,
        }

    def get_data_source_status(self) -> dict:
        return self._last_status

    def _normalize_history(self, history: pd.DataFrame | None) -> pd.DataFrame:
        if history is None or history.empty:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

        normalized = history.reset_index()
        column_map = {
            "index": "date",
            "Date": "date",
            "Datetime": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
        normalized = normalized.rename(columns=column_map)
        required_columns = ["date", "open", "high", "low", "close", "volume"]
        for column in required_columns:
            if column not in normalized:
                normalized[column] = None

        normalized = normalized[required_columns].dropna(subset=["close"])
        normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce").dt.date.astype(str)
        for column in ["open", "high", "low", "close", "volume"]:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
        normalized = normalized[normalized["date"] != "NaT"]
        return normalized.dropna(subset=["close"]).reset_index(drop=True)

    def _fallback_history(self, ticker: str, market: MarketCode, warning: str) -> pd.DataFrame:
        fallback_history = self.fallback_provider.get_price_history(ticker=ticker, market=market)
        self._last_status = self._status(
            quality="DEGRADED" if not fallback_history.empty else "UNAVAILABLE",
            status="DEGRADED" if not fallback_history.empty else "DOWN",
            normalized_ticker=normalize_yfinance_ticker(ticker=ticker, market=market),
            fallback_used=not fallback_history.empty,
            warnings=[warning, "yfinance data unavailable; fallback mock data used."],
        )
        return fallback_history

    def _read_fast_info_price(self, fast_info: Any) -> float | None:
        for key in ("last_price", "lastPrice", "regularMarketPrice"):
            try:
                value = fast_info[key] if isinstance(fast_info, dict) else getattr(fast_info, key)
            except (KeyError, AttributeError):
                continue
            if value is not None:
                return float(value)
        return None

    def _status(
        self,
        quality: str,
        status: str,
        warnings: list[str],
        normalized_ticker: str | None = None,
        fallback_used: bool = False,
    ) -> dict:
        return {
            "provider_name": self.provider_name,
            "status": status,
            "quality": quality,
            "message": "yfinance provider selected.",
            "is_mock": fallback_used,
            "fallback_used": fallback_used,
            "normalized_ticker": normalized_ticker,
            "warnings": warnings,
        }

    def _append_warning(self, warning: str) -> None:
        warnings = list(self._last_status.get("warnings", []))
        warnings.append(warning)
        self._last_status = {
            **self._last_status,
            "warnings": warnings,
        }
