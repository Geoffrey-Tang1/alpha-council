from app.agents.base import BaseAgent
from app.core.constants import MarketCode
from app.data_providers.base import MarketDataProvider
from app.financial_data.provider_registry import get_financial_data_adapter
from app.financial_data.schemas import FinancialDataSnapshot
from app.services.financial_data_service import FinancialDataService
from app.services.market_status_service import MarketStatusService
from app.services.news_research_service import NewsResearchService


class DataCollectorAgent(BaseAgent):
    name = "data_collector"

    def __init__(
        self,
        provider: MarketDataProvider,
        market_status_service: MarketStatusService | None = None,
        financial_data_service: FinancialDataService | None = None,
        news_research_service: NewsResearchService | None = None,
    ) -> None:
        self.provider = provider
        self.market_status_service = market_status_service or MarketStatusService()
        self.financial_data_service = financial_data_service or FinancialDataService(
            adapter=get_financial_data_adapter(provider)
        )
        self.news_research_service = news_research_service or NewsResearchService()

    def collect(self, ticker: str, market: MarketCode) -> dict:
        financial_data = self.financial_data_service.get_research_snapshot(ticker=ticker, market=market)
        news_research = self.news_research_service.get_sentiment_snapshot(ticker=ticker, market=market)
        price_history = self._price_history_dataframe(financial_data)
        latest_price = financial_data.quote.last_price
        fundamentals = self._legacy_fundamentals(financial_data)
        company_profile = self._legacy_company_profile(financial_data)
        return {
            "ticker": ticker,
            "market": market,
            "latest_price": latest_price,
            "price_history": price_history,
            "company_profile": company_profile,
            "fundamentals": fundamentals,
            "news": self._legacy_news(news_research),
            "news_research": news_research,
            "macro_context": self.provider.get_macro_context(market=market),
            "data_source_status": self.provider.get_data_source_status(),
            "market_status": self.market_status_service.get_market_status(market=market),
            "financial_data": financial_data,
        }

    def _price_history_dataframe(self, financial_data: FinancialDataSnapshot):
        history = financial_data.price_history.to_dataframe()
        if history.empty:
            return history
        return history[["date", "open", "high", "low", "close", "volume"]]

    def _legacy_news(self, news_research) -> list[dict]:
        if not news_research.articles:
            return [
                {
                    "headline": reason,
                    "source": news_research.provider,
                    "sentiment": news_research.sentiment_label,
                    "is_mock": news_research.provider == "mock",
                }
                for reason in news_research.unavailable_reasons
            ]
        return [
            {
                "headline": article.title,
                "source": article.provider,
                "sentiment": news_research.sentiment_label,
                "is_mock": article.source_type.value == "mock_data",
            }
            for article in news_research.articles
        ]

    def _legacy_company_profile(self, financial_data: FinancialDataSnapshot) -> dict:
        profile = financial_data.company_profile
        instrument = financial_data.instrument
        return {
            "ticker": instrument.symbol,
            "market": instrument.market.value,
            "normalized_ticker": instrument.provider_symbol,
            "display_symbol": instrument.display_symbol,
            "company_name": profile.display_name,
            "sector": profile.sector,
            "industry": profile.industry,
            "exchange": profile.exchange,
            "currency": profile.currency,
            "is_mock": financial_data.provider == "mock",
        }

    def _legacy_fundamentals(self, financial_data: FinancialDataSnapshot) -> dict:
        fundamentals = financial_data.financial_metrics.by_name()
        valuation = financial_data.valuation_metrics.by_name()
        return {
            **fundamentals,
            "revenue_growth": fundamentals.get("revenue_growth_yoy"),
            "profit_margins": fundamentals.get("operating_margin"),
            "trailing_pe": valuation.get("price_to_earnings"),
            "forward_pe": valuation.get("forward_price_to_earnings"),
            "price_to_sales": valuation.get("price_to_sales"),
            "price_to_book": valuation.get("price_to_book"),
            "is_mock": financial_data.provider == "mock",
            "availability_status": financial_data.financial_metrics.availability_status.value,
            "freshness_status": financial_data.financial_metrics.freshness_status.value,
        }
