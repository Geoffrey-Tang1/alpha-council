import os

from app.news_research.providers.base import NewsResearchProvider
from app.news_research.providers.disabled import DisabledNewsProvider
from app.news_research.providers.mock import MockNewsProvider
from app.news_research.providers.placeholder import PlaceholderNewsProvider


PLACEHOLDER_PROVIDERS = {"rss", "gdelt", "yfinance", "openalex"}


def get_news_research_provider() -> NewsResearchProvider:
    selected = os.getenv("NEWS_RESEARCH_PROVIDER", "auto").strip().lower()
    data_provider = os.getenv("DATA_PROVIDER", "mock").strip().lower()

    if selected == "auto":
        return MockNewsProvider() if data_provider == "mock" else DisabledNewsProvider()
    if selected == "mock":
        return MockNewsProvider()
    if selected == "disabled":
        return DisabledNewsProvider()
    if selected in PLACEHOLDER_PROVIDERS:
        return PlaceholderNewsProvider(selected)

    return DisabledNewsProvider(
        extra_warnings=[f"Unknown NEWS_RESEARCH_PROVIDER '{selected}'; news research provider is disabled."]
    )
