from app.agents.base import BaseAgent
from app.core.constants import AgentSignal
from app.schemas.agents import NewsSentimentOutput


class NewsSentimentAgent(BaseAgent):
    name = "news_sentiment"

    def analyze(self, collected_data: dict) -> NewsSentimentOutput:
        news_items = collected_data["news"]
        data_sources = sorted({item["source"] for item in news_items}) or ["unknown"]
        uses_mock = any(item.get("is_mock") for item in news_items)
        explanation = (
            "Mock news flow is neutral; no verified external news API is connected."
            if uses_mock
            else "News flow is sourced from yfinance when available; sentiment remains placeholder logic."
        )
        risks = (
            ["News and sentiment are placeholders.", "Catalyst timing is not verified."]
            if uses_mock
            else ["yfinance news may be sparse or unavailable.", "Sentiment scoring is placeholder logic."]
        )
        return NewsSentimentOutput(
            sentiment_signal=AgentSignal.WATCH,
            confidence=0.5,
            explanation=explanation,
            catalysts=["Future real news provider can add earnings, announcements, and analyst changes."],
            risks=risks,
            data_sources=data_sources,
        )
