from app.agents.base import BaseAgent
from app.core.constants import AgentSignal
from app.news_research.schemas import NewsAvailability, NewsSentimentSnapshot, NewsSourceType
from app.schemas.agents import NewsSentimentOutput


class NewsSentimentAgent(BaseAgent):
    name = "news_sentiment"

    def analyze(self, collected_data: dict) -> NewsSentimentOutput:
        snapshot = self._snapshot(collected_data)
        if snapshot is not None:
            return self._from_snapshot(snapshot)

        news_items = collected_data.get("news", [])
        data_sources = sorted({item.get("source", "unknown") for item in news_items}) or ["unknown"]
        return NewsSentimentOutput(
            sentiment_signal=AgentSignal.WATCH,
            confidence=0.2,
            explanation="Verified news/research provider snapshot is unavailable.",
            catalysts=[],
            risks=["News provider snapshot missing; verified news and sentiment are unavailable."],
            data_sources=data_sources,
            provider="unknown",
            article_count=len(news_items),
            availability="unavailable",
            freshness="unknown",
            sentiment_available=False,
            sentiment_label="unavailable",
            sentiment_method="not_computed",
            source_type="unavailable_source",
            unavailable_reasons=["News provider snapshot missing."],
            warnings=["News provider snapshot missing."],
        )

    def _snapshot(self, collected_data: dict) -> NewsSentimentSnapshot | None:
        raw = collected_data.get("news_research")
        if raw is None:
            return None
        if isinstance(raw, NewsSentimentSnapshot):
            return raw
        try:
            return NewsSentimentSnapshot.model_validate(raw)
        except Exception:
            return None

    def _from_snapshot(self, snapshot: NewsSentimentSnapshot) -> NewsSentimentOutput:
        provider = snapshot.provider
        article_count = len(snapshot.articles)
        data_sources = sorted({article.provider for article in snapshot.articles}) or [provider]
        source_type = self._source_type(snapshot)
        warnings = list(dict.fromkeys([*snapshot.warnings, *snapshot.unavailable_reasons]))

        if snapshot.availability == NewsAvailability.UNAVAILABLE:
            return NewsSentimentOutput(
                sentiment_signal=AgentSignal.WATCH,
                confidence=0.18,
                explanation="Verified news and research sources are unavailable for this instrument.",
                catalysts=[],
                risks=warnings or ["No verified news source is connected."],
                data_sources=data_sources,
                provider=provider,
                article_count=article_count,
                fetched_at=snapshot.fetched_at,
                availability=snapshot.availability.value,
                freshness=snapshot.freshness.value,
                sentiment_available=False,
                sentiment_label=snapshot.sentiment_label,
                sentiment_method=snapshot.sentiment_method,
                source_type=source_type,
                unavailable_reasons=snapshot.unavailable_reasons,
                warnings=warnings,
            )

        if provider == "mock":
            return NewsSentimentOutput(
                sentiment_signal=AgentSignal.WATCH,
                confidence=0.32,
                explanation=(
                    "Mock news/research source is available for workflow testing only; "
                    "no verified external news is connected."
                ),
                catalysts=["Mock source flags no verified investable catalyst."],
                risks=warnings,
                data_sources=data_sources,
                provider=provider,
                article_count=article_count,
                fetched_at=snapshot.fetched_at,
                availability=snapshot.availability.value,
                freshness=snapshot.freshness.value,
                sentiment_available=snapshot.sentiment_available,
                sentiment_label=snapshot.sentiment_label,
                sentiment_method=snapshot.sentiment_method,
                source_type=source_type,
                unavailable_reasons=snapshot.unavailable_reasons,
                warnings=warnings,
            )

        sentiment_note = (
            f"Sentiment label is {snapshot.sentiment_label} using {snapshot.sentiment_method}."
            if snapshot.sentiment_available
            else "Sentiment is unavailable; it is not inferred from missing or insufficient data."
        )
        return NewsSentimentOutput(
            sentiment_signal=AgentSignal.WATCH,
            confidence=0.45 if snapshot.sentiment_available else 0.28,
            explanation=f"News/research provider returned {article_count} article(s). {sentiment_note}",
            catalysts=[article.title for article in snapshot.articles[:3] if article.title],
            risks=warnings or ["News coverage may be incomplete."],
            data_sources=data_sources,
            provider=provider,
            article_count=article_count,
            fetched_at=snapshot.fetched_at,
            availability=snapshot.availability.value,
            freshness=snapshot.freshness.value,
            sentiment_available=snapshot.sentiment_available,
            sentiment_label=snapshot.sentiment_label,
            sentiment_method=snapshot.sentiment_method,
            source_type=source_type,
            unavailable_reasons=snapshot.unavailable_reasons,
            warnings=warnings,
        )

    def _source_type(self, snapshot: NewsSentimentSnapshot) -> str:
        if snapshot.articles:
            article_type = snapshot.articles[0].source_type
            return article_type.value if isinstance(article_type, NewsSourceType) else str(article_type)
        if snapshot.provider == "mock":
            return NewsSourceType.MOCK_DATA.value
        return NewsSourceType.UNAVAILABLE_SOURCE.value
