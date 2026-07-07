from abc import ABC, abstractmethod
from datetime import date

import pandas as pd

from app.core.constants import MarketCode


class MarketDataProvider(ABC):
    @abstractmethod
    def get_latest_price(self, ticker: str, market: MarketCode) -> float | None:
        raise NotImplementedError

    @abstractmethod
    def get_price_history(
        self,
        ticker: str,
        market: MarketCode,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def get_company_profile(self, ticker: str, market: MarketCode) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_fundamentals(self, ticker: str, market: MarketCode) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_news(self, ticker: str, market: MarketCode, limit: int = 5) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_macro_context(self, market: MarketCode) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_data_source_status(self) -> dict:
        raise NotImplementedError
