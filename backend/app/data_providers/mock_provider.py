from datetime import date, timedelta
import hashlib

import numpy as np
import pandas as pd

from app.core.constants import MarketCode
from app.data_providers.base import MarketDataProvider
from app.data_providers.instrument_metadata import build_instrument_metadata


class MockDataProvider(MarketDataProvider):
    """Deterministic local provider used for Phase 1 development and tests."""

    provider_name = "mock"

    def __init__(self, registry_warnings: list[str] | None = None) -> None:
        self.registry_warnings = registry_warnings or []

    def _seed(self, ticker: str, market: MarketCode) -> int:
        key = f"{ticker.upper()}:{market.value}".encode("utf-8")
        return int(hashlib.sha256(key).hexdigest()[:8], 16)

    def get_price_history(
        self,
        ticker: str,
        market: MarketCode,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        seed = self._seed(ticker, market)
        rng = np.random.default_rng(seed)
        end_date = end or date.today()
        days = 120
        start_date = start or (end_date - timedelta(days=days * 2))
        business_dates = pd.bdate_range(start=start_date, end=end_date)[-days:]

        base_price = 30 + (seed % 220)
        trend = np.linspace(0, (seed % 30) / 10, len(business_dates))
        seasonal = np.sin(np.linspace(0, 8, len(business_dates))) * 2.5
        noise = rng.normal(0, 1.2, len(business_dates)).cumsum() * 0.25
        close = np.maximum(base_price + trend + seasonal + noise, 1)
        open_price = close * (1 + rng.normal(0, 0.004, len(close)))
        high = np.maximum(open_price, close) * (1 + rng.uniform(0.002, 0.018, len(close)))
        low = np.minimum(open_price, close) * (1 - rng.uniform(0.002, 0.018, len(close)))
        volume = rng.integers(500_000, 8_000_000, len(close))

        return pd.DataFrame(
            {
                "date": business_dates.date.astype(str),
                "open": open_price.round(2),
                "high": high.round(2),
                "low": low.round(2),
                "close": close.round(2),
                "volume": volume,
            }
        )

    def get_latest_price(self, ticker: str, market: MarketCode) -> float | None:
        history = self.get_price_history(ticker=ticker, market=market)
        if history.empty:
            return None
        return float(history.iloc[-1]["close"])

    def get_company_profile(self, ticker: str, market: MarketCode) -> dict:
        metadata = build_instrument_metadata(ticker=ticker, market=market)
        return {
            "ticker": metadata["ticker"],
            "market": market.value,
            "normalized_ticker": metadata["normalized_ticker"],
            "display_symbol": metadata["display_symbol"],
            "company_name": metadata["company_name"],
            "sector": "Technology",
            "industry": "Semiconductors and Software",
            "is_mock": True,
        }

    def get_fundamentals(self, ticker: str, market: MarketCode) -> dict:
        seed = self._seed(ticker, market)
        return {
            "revenue_growth_yoy": round(0.04 + (seed % 16) / 100, 3),
            "operating_margin": round(0.12 + (seed % 18) / 100, 3),
            "debt_to_equity": round(0.15 + (seed % 60) / 100, 3),
            "free_cash_flow_margin": round(0.08 + (seed % 14) / 100, 3),
            "market_cap": float(25_000_000_000 + (seed % 400) * 100_000_000),
            "trailing_pe": round(18 + (seed % 25), 2),
            "forward_pe": round(16 + (seed % 20), 2),
            "price_to_sales": round(3 + (seed % 12) / 2, 2),
            "price_to_book": round(2 + (seed % 10) / 2, 2),
            "dividend_yield": round((seed % 4) / 100, 4),
            "valuation_label": "fair",
            "is_mock": True,
        }

    def get_news(self, ticker: str, market: MarketCode, limit: int = 5) -> list[dict]:
        headlines = [
            "Management commentary remains constructive but not definitive.",
            "Sector demand indicators are mixed in the latest mock update.",
            "Analysts are watching margin stability and capital allocation.",
            "No verified breaking news source is connected in Phase 1.",
            "Mock catalyst calendar flags no confirmed near-term event.",
        ]
        return [
            {
                "headline": f"{ticker.upper()}: {headline}",
                "source": "mock_news",
                "sentiment": "neutral",
                "is_mock": True,
            }
            for headline in headlines[:limit]
        ]

    def get_macro_context(self, market: MarketCode) -> dict:
        context_by_market = {
            MarketCode.US: "US rates and mega-cap risk appetite remain key drivers.",
            MarketCode.JP: "Yen sensitivity and exporter sentiment remain relevant.",
            MarketCode.TW: "Semiconductor cycle and USD/TWD conditions matter.",
            MarketCode.KR: "Memory cycle and KRW sensitivity remain relevant.",
        }
        return {
            "risk_environment": "neutral",
            "summary": context_by_market.get(market, "Macro context unavailable."),
            "is_mock": True,
        }

    def get_data_source_status(self) -> dict:
        return {
            "provider_name": self.provider_name,
            "status": "OK",
            "quality": "MOCK",
            "message": "Deterministic mock provider is available.",
            "is_mock": True,
            "warnings": [
                "MVP Mode: using deterministic mock data. Not real market data.",
                *self.registry_warnings,
            ],
        }
