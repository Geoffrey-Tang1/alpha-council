from app.agents.base import BaseAgent
from app.core.constants import AgentSignal
from app.schemas.agents import NewsSentimentOutput


class NewsSentimentAgent(BaseAgent):
    name = "news_sentiment"

    def analyze(self, collected_data: dict) -> NewsSentimentOutput:
        news_items = collected_data["news"]
        return NewsSentimentOutput(
            sentiment_signal=AgentSignal.WATCH,
            confidence=0.5,
            explanation="Mock news flow is neutral; no verified external news API is connected in Phase 1.",
            catalysts=["Future real news provider can add earnings, announcements, and analyst changes."],
            risks=["News and sentiment are placeholders.", "Catalyst timing is not verified."],
            data_sources=sorted({item["source"] for item in news_items}) or ["mock_news"],
        )
