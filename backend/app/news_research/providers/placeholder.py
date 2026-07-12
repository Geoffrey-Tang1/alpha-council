from app.news_research.providers.disabled import DisabledNewsProvider


class PlaceholderNewsProvider(DisabledNewsProvider):
    supports_live_news = False
    supports_sentiment = False

    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name
        super().__init__(
            extra_warnings=[
                f"News provider '{provider_name}' is a future integration placeholder and is not implemented in this phase."
            ]
        )

