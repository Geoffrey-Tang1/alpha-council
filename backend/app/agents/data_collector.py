from app.agents.base import BaseAgent
from app.core.constants import MarketCode
from app.data_providers.base import MarketDataProvider
from app.services.market_status_service import MarketStatusService


class DataCollectorAgent(BaseAgent):
    name = "data_collector"

    def __init__(
        self,
        provider: MarketDataProvider,
        market_status_service: MarketStatusService | None = None,
    ) -> None:
        self.provider = provider
        self.market_status_service = market_status_service or MarketStatusService()

    def collect(self, ticker: str, market: MarketCode) -> dict:
        price_history = self.provider.get_price_history(ticker=ticker, market=market)
        latest_price = self.provider.get_latest_price(ticker=ticker, market=market)
        return {
            "ticker": ticker,
            "market": market,
            "latest_price": latest_price,
            "price_history": price_history,
            "company_profile": self.provider.get_company_profile(ticker=ticker, market=market),
            "fundamentals": self.provider.get_fundamentals(ticker=ticker, market=market),
            "news": self.provider.get_news(ticker=ticker, market=market),
            "macro_context": self.provider.get_macro_context(market=market),
            "data_source_status": self.provider.get_data_source_status(),
            "market_status": self.market_status_service.get_market_status(market=market),
        }
