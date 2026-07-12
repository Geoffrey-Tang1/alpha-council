from app.core.constants import MarketCode
from app.news_research.provider_registry import get_news_research_provider
from app.news_research.providers.base import NewsResearchProvider
from app.news_research.schemas import NewsArticleListResponse, NewsResearchStatus, NewsSentimentSnapshot


class NewsResearchService:
    def __init__(self, provider: NewsResearchProvider | None = None) -> None:
        self.provider = provider or get_news_research_provider()

    def status(self) -> NewsResearchStatus:
        return self.provider.status()

    def get_articles(self, ticker: str, market: MarketCode, limit: int = 10) -> NewsArticleListResponse:
        try:
            return self.provider.get_articles(ticker=ticker, market=market, limit=limit)
        except Exception as exc:
            from app.news_research.providers.disabled import DisabledNewsProvider

            disabled = DisabledNewsProvider()
            response = disabled.get_articles(ticker=ticker, market=market, limit=limit)
            warning = f"News provider failed safely: {type(exc).__name__}."
            return response.model_copy(
                update={
                    "warnings": [warning, *response.warnings],
                    "unavailable_reasons": [warning, *response.unavailable_reasons],
                }
            )

    def get_sentiment_snapshot(self, ticker: str, market: MarketCode, limit: int = 10) -> NewsSentimentSnapshot:
        try:
            return self.provider.get_sentiment_snapshot(ticker=ticker, market=market, limit=limit)
        except Exception as exc:
            from app.news_research.providers.disabled import DisabledNewsProvider

            response = DisabledNewsProvider().get_sentiment_snapshot(ticker=ticker, market=market, limit=limit)
            warning = f"News sentiment provider failed safely: {type(exc).__name__}."
            return response.model_copy(
                update={
                    "warnings": [warning, *response.warnings],
                    "unavailable_reasons": [warning, *response.unavailable_reasons],
                }
            )
