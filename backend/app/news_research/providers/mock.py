from app.core.constants import MarketCode
from app.news_research.providers.base import NewsResearchProvider
from app.news_research.schemas import (
    NewsArticle,
    NewsArticleListResponse,
    NewsAvailability,
    NewsFreshness,
    NewsResearchStatus,
    NewsSentimentSnapshot,
    NewsSourceType,
    utc_now_iso,
)


MOCK_WARNING = "Mock news provider returns deterministic development data only; no verified external news is connected."


class MockNewsProvider(NewsResearchProvider):
    provider_name = "mock"
    supports_live_news = False
    supports_sentiment = True

    def status(self) -> NewsResearchStatus:
        return NewsResearchStatus(
            provider=self.provider_name,
            enabled=True,
            supports_live_news=False,
            supports_sentiment=True,
            cache_status={"enabled": False, "provider": self.provider_name},
            warnings=[MOCK_WARNING],
            unavailable_reasons=[],
            fetched_at=utc_now_iso(),
        )

    def get_articles(self, ticker: str, market: MarketCode, limit: int = 10) -> NewsArticleListResponse:
        fetched_at = utc_now_iso()
        symbol = ticker.upper()
        titles = [
            "Mock monitoring note: verified company news feed unavailable",
            "Mock research note: no real announcement source connected",
            "Mock catalyst placeholder: earnings calendar unavailable",
        ]
        articles = [
            NewsArticle(
                article_id=f"mock_{symbol}_{index}",
                provider=self.provider_name,
                provider_article_id=f"mock_{index}",
                title=f"{symbol}: {title}",
                summary=(
                    "Development-only mock news item. This is not a real article, "
                    "not a verified source, and not suitable for investment conclusions."
                ),
                url=None,
                publisher="Wisoka Compass Mock Provider",
                author=None,
                published_at=None,
                fetched_at=fetched_at,
                tickers=[symbol],
                market=market,
                language="en",
                source_type=NewsSourceType.MOCK_DATA,
                availability=NewsAvailability.PARTIAL,
                freshness=NewsFreshness.MOCK,
                is_verified_url=False,
                is_paywalled=None,
                warnings=[MOCK_WARNING, "No clickable URL is provided because this is not real news."],
            )
            for index, title in enumerate(titles[:limit], start=1)
        ]
        return NewsArticleListResponse(
            symbol=symbol,
            market=market,
            provider=self.provider_name,
            fetched_at=fetched_at,
            articles=articles,
            availability=NewsAvailability.PARTIAL,
            warnings=[MOCK_WARNING],
            unavailable_reasons=["Verified live news is not configured."],
        )

    def get_sentiment_snapshot(self, ticker: str, market: MarketCode, limit: int = 10) -> NewsSentimentSnapshot:
        article_response = self.get_articles(ticker=ticker, market=market, limit=limit)
        return NewsSentimentSnapshot(
            symbol=article_response.symbol,
            market=market,
            provider=self.provider_name,
            fetched_at=article_response.fetched_at,
            articles=article_response.articles,
            sentiment_available=False,
            sentiment_score=None,
            sentiment_label="mock_unavailable",
            sentiment_method="not_computed_mock_data",
            availability=NewsAvailability.PARTIAL,
            freshness=NewsFreshness.MOCK,
            warnings=[
                *article_response.warnings,
                "Sentiment is unavailable because mock articles are not verified external news.",
            ],
            unavailable_reasons=article_response.unavailable_reasons,
        )
