from fastapi import APIRouter, Query

from app.core.constants import MarketCode
from app.news_research.schemas import NewsArticleListResponse, NewsResearchStatus, NewsSentimentSnapshot
from app.services.news_research_service import NewsResearchService

router = APIRouter(prefix="/news-research", tags=["news-research"])


@router.get("/status", response_model=NewsResearchStatus)
def news_research_status() -> NewsResearchStatus:
    return NewsResearchService().status()


@router.get("/articles", response_model=NewsArticleListResponse)
def get_articles(
    ticker: str = Query(min_length=1),
    market: MarketCode = Query(),
    limit: int = Query(default=10, ge=0, le=25),
) -> NewsArticleListResponse:
    return NewsResearchService().get_articles(ticker=ticker, market=market, limit=limit)


@router.get("/sentiment", response_model=NewsSentimentSnapshot)
def get_sentiment(
    ticker: str = Query(min_length=1),
    market: MarketCode = Query(),
    limit: int = Query(default=10, ge=0, le=25),
) -> NewsSentimentSnapshot:
    return NewsResearchService().get_sentiment_snapshot(ticker=ticker, market=market, limit=limit)

