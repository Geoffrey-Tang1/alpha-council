from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.constants import MarketCode


NEWS_RESEARCH_SCHEMA_VERSION = "news_research_v1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class NewsAvailability(StrEnum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class NewsFreshness(StrEnum):
    CURRENT = "current"
    DELAYED = "delayed"
    STALE = "stale"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    MOCK = "mock"


class NewsSourceType(StrEnum):
    NEWS_PROVIDER = "news_provider"
    RESEARCH_PROVIDER = "research_provider"
    MOCK_DATA = "mock_data"
    UNAVAILABLE_SOURCE = "unavailable_source"


class NewsArticle(BaseModel):
    article_id: str
    provider: str
    provider_article_id: str | None = None
    title: str
    summary: str | None = None
    url: str | None = None
    publisher: str | None = None
    author: str | None = None
    published_at: str | None = None
    fetched_at: str
    tickers: list[str] = Field(default_factory=list)
    market: MarketCode
    language: str | None = None
    source_type: NewsSourceType
    availability: NewsAvailability
    freshness: NewsFreshness
    is_verified_url: bool = False
    is_paywalled: bool | None = None
    warnings: list[str] = Field(default_factory=list)


class ResearchSource(BaseModel):
    source_id: str
    provider: str
    title: str
    url: str | None = None
    publisher: str | None = None
    source_type: NewsSourceType
    published_at: str | None = None
    fetched_at: str
    related_symbols: list[str] = Field(default_factory=list)
    availability: NewsAvailability
    freshness: NewsFreshness
    warnings: list[str] = Field(default_factory=list)


class NewsArticleListResponse(BaseModel):
    schema_version: str = NEWS_RESEARCH_SCHEMA_VERSION
    symbol: str
    market: MarketCode
    provider: str
    fetched_at: str
    articles: list[NewsArticle] = Field(default_factory=list)
    availability: NewsAvailability
    warnings: list[str] = Field(default_factory=list)
    unavailable_reasons: list[str] = Field(default_factory=list)


class NewsSentimentSnapshot(BaseModel):
    schema_version: str = NEWS_RESEARCH_SCHEMA_VERSION
    symbol: str
    market: MarketCode
    provider: str
    fetched_at: str
    articles: list[NewsArticle] = Field(default_factory=list)
    sentiment_available: bool = False
    sentiment_score: float | None = Field(default=None, ge=-1, le=1)
    sentiment_label: str = "unavailable"
    sentiment_method: str = "not_computed"
    availability: NewsAvailability
    freshness: NewsFreshness
    warnings: list[str] = Field(default_factory=list)
    unavailable_reasons: list[str] = Field(default_factory=list)


class NewsResearchStatus(BaseModel):
    schema_version: str = NEWS_RESEARCH_SCHEMA_VERSION
    provider: str
    enabled: bool
    supports_live_news: bool
    supports_sentiment: bool
    cache_status: dict[str, str | int | bool] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    unavailable_reasons: list[str] = Field(default_factory=list)
    fetched_at: str

