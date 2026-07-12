from app.core.constants import MarketCode
from app.news_research.providers.base import NewsResearchProvider
from app.news_research.schemas import (
    NewsArticleListResponse,
    NewsAvailability,
    NewsFreshness,
    NewsResearchStatus,
    NewsSentimentSnapshot,
    utc_now_iso,
)


DISABLED_MESSAGE = "News provider is disabled. No verified news sources are available."


class DisabledNewsProvider(NewsResearchProvider):
    provider_name = "disabled"
    supports_live_news = False
    supports_sentiment = False

    def __init__(self, extra_warnings: list[str] | None = None) -> None:
        self.extra_warnings = extra_warnings or []

    def _warnings(self) -> list[str]:
        return [*self.extra_warnings, DISABLED_MESSAGE]

    def status(self) -> NewsResearchStatus:
        return NewsResearchStatus(
            provider=self.provider_name,
            enabled=False,
            supports_live_news=False,
            supports_sentiment=False,
            cache_status={"enabled": False, "provider": self.provider_name},
            warnings=self._warnings(),
            unavailable_reasons=self._warnings(),
            fetched_at=utc_now_iso(),
        )

    def get_articles(self, ticker: str, market: MarketCode, limit: int = 10) -> NewsArticleListResponse:
        return NewsArticleListResponse(
            symbol=ticker.upper(),
            market=market,
            provider=self.provider_name,
            fetched_at=utc_now_iso(),
            articles=[],
            availability=NewsAvailability.UNAVAILABLE,
            warnings=self._warnings(),
            unavailable_reasons=self._warnings(),
        )

    def get_sentiment_snapshot(self, ticker: str, market: MarketCode, limit: int = 10) -> NewsSentimentSnapshot:
        fetched_at = utc_now_iso()
        return NewsSentimentSnapshot(
            symbol=ticker.upper(),
            market=market,
            provider=self.provider_name,
            fetched_at=fetched_at,
            articles=[],
            sentiment_available=False,
            sentiment_score=None,
            sentiment_label="unavailable",
            sentiment_method="not_computed",
            availability=NewsAvailability.UNAVAILABLE,
            freshness=NewsFreshness.UNAVAILABLE,
            warnings=self._warnings(),
            unavailable_reasons=self._warnings(),
        )
