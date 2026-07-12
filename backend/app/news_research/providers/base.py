from abc import ABC, abstractmethod

from app.core.constants import MarketCode
from app.news_research.schemas import NewsArticleListResponse, NewsResearchStatus, NewsSentimentSnapshot


class NewsResearchProvider(ABC):
    provider_name: str
    supports_live_news: bool = False
    supports_sentiment: bool = False

    @abstractmethod
    def status(self) -> NewsResearchStatus:
        raise NotImplementedError

    @abstractmethod
    def get_articles(self, ticker: str, market: MarketCode, limit: int = 10) -> NewsArticleListResponse:
        raise NotImplementedError

    @abstractmethod
    def get_sentiment_snapshot(self, ticker: str, market: MarketCode, limit: int = 10) -> NewsSentimentSnapshot:
        raise NotImplementedError

