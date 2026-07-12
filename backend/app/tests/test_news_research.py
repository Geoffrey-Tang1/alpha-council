from app.agents.news_sentiment import NewsSentimentAgent
from app.core.constants import MarketCode
from app.news_research.provider_registry import get_news_research_provider
from app.news_research.providers.disabled import DISABLED_MESSAGE, DisabledNewsProvider
from app.news_research.providers.mock import MOCK_WARNING, MockNewsProvider
from app.news_research.schemas import NewsAvailability, NewsSourceType
from app.schemas.analysis import AnalysisRequest
from app.services.analysis_service import AnalysisService


def test_disabled_news_provider_returns_unavailable():
    provider = DisabledNewsProvider()

    status = provider.status()
    articles = provider.get_articles("NVDA", MarketCode.US)
    snapshot = provider.get_sentiment_snapshot("NVDA", MarketCode.US)

    assert status.enabled is False
    assert status.supports_live_news is False
    assert DISABLED_MESSAGE in status.warnings
    assert articles.availability == NewsAvailability.UNAVAILABLE
    assert articles.articles == []
    assert snapshot.sentiment_available is False
    assert snapshot.sentiment_label == "unavailable"
    assert DISABLED_MESSAGE in snapshot.unavailable_reasons


def test_mock_news_provider_is_deterministic_and_not_real_news():
    provider = MockNewsProvider()

    articles = provider.get_articles("NVDA", MarketCode.US)
    snapshot = provider.get_sentiment_snapshot("NVDA", MarketCode.US)

    assert articles.provider == "mock"
    assert articles.availability == NewsAvailability.PARTIAL
    assert articles.articles
    assert all(article.source_type == NewsSourceType.MOCK_DATA for article in articles.articles)
    assert all(article.url is None for article in articles.articles)
    assert all(article.is_verified_url is False for article in articles.articles)
    assert MOCK_WARNING in articles.warnings
    assert snapshot.sentiment_available is False
    assert snapshot.sentiment_label == "mock_unavailable"
    assert snapshot.sentiment_method == "not_computed_mock_data"
    assert any("mock articles are not verified external news" in warning for warning in snapshot.warnings)


def test_news_provider_registry_auto_uses_mock_for_mock_data(monkeypatch):
    monkeypatch.setenv("DATA_PROVIDER", "mock")
    monkeypatch.setenv("NEWS_RESEARCH_PROVIDER", "auto")

    assert get_news_research_provider().provider_name == "mock"


def test_news_provider_registry_auto_disables_for_yfinance(monkeypatch):
    monkeypatch.setenv("DATA_PROVIDER", "yfinance")
    monkeypatch.setenv("NEWS_RESEARCH_PROVIDER", "auto")

    assert get_news_research_provider().provider_name == "disabled"


def test_placeholder_news_provider_is_unavailable(monkeypatch):
    monkeypatch.setenv("NEWS_RESEARCH_PROVIDER", "gdelt")

    provider = get_news_research_provider()
    status = provider.status()

    assert provider.provider_name == "gdelt"
    assert status.enabled is False
    assert any("future integration placeholder" in warning for warning in status.warnings)


def test_news_research_status_endpoint(client):
    response = client.get("/api/v1/news-research/status")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["supports_live_news"] is False
    assert body["supports_sentiment"] is True
    assert body["warnings"]


def test_news_research_articles_endpoint_returns_mock_without_fake_urls(client):
    response = client.get("/api/v1/news-research/articles?ticker=NVDA&market=US")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["availability"] == "partial"
    assert body["articles"]
    assert all(article["source_type"] == "mock_data" for article in body["articles"])
    assert all(article["url"] is None for article in body["articles"])
    assert all(article["is_verified_url"] is False for article in body["articles"])


def test_news_research_sentiment_endpoint_marks_mock_sentiment(client):
    response = client.get("/api/v1/news-research/sentiment?ticker=NVDA&market=US")

    assert response.status_code == 200
    body = response.json()
    assert body["sentiment_available"] is False
    assert body["sentiment_label"] == "mock_unavailable"
    assert body["sentiment_method"] == "not_computed_mock_data"
    assert body["unavailable_reasons"] == ["Verified live news is not configured."]


def test_news_sentiment_agent_uses_snapshot_without_fake_citations():
    snapshot = DisabledNewsProvider().get_sentiment_snapshot("NVDA", MarketCode.US)

    output = NewsSentimentAgent().analyze({"news_research": snapshot})

    assert output.provider == "disabled"
    assert output.article_count == 0
    assert output.sentiment_available is False
    assert output.availability == "unavailable"
    assert output.catalysts == []
    assert DISABLED_MESSAGE in output.unavailable_reasons


def test_research_report_contains_news_research_evidence_without_fake_urls(client):
    response = client.post(
        "/api/v1/analysis/run",
        json={
            "ticker": "NVDA",
            "market": "US",
            "time_horizon": "swing",
            "strategy_preference": "moving_average_crossover",
        },
    )

    assert response.status_code == 200
    report = response.json()["research_report"]
    news_items = [item for item in report["evidence"] if item["category"] == "news_research"]
    assert news_items
    assert any(item["title"] == "Verified news feed" for item in news_items)
    assert any(item["source_type"] == "mock_data" for item in news_items)
    assert not any(item.get("source_reference") for item in news_items)
    assert "catalysts" not in [
        dimension["name"]
        for dimension in report["research_plan"]["dimensions"]
        if dimension["status"] == "available"
    ]


def test_analysis_service_with_disabled_news_provider_reports_unavailable(monkeypatch):
    monkeypatch.setenv("NEWS_RESEARCH_PROVIDER", "disabled")
    service = AnalysisService()

    decision = service.run_analysis(
        AnalysisRequest(
            ticker="NVDA",
            market=MarketCode.US,
            time_horizon="swing",
            strategy_preference="moving_average_crossover",
        )
    )

    assert decision.agent_outputs.news_sentiment.provider == "disabled"
    assert decision.agent_outputs.news_sentiment.sentiment_available is False
    assert decision.research_report is not None
    news_items = [item for item in decision.research_report.evidence if item.category == "news_research"]
    assert any(item.title == "Verified news feed" and item.source_reference is None for item in news_items)
