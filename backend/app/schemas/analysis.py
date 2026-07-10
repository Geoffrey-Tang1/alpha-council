from pydantic import BaseModel, Field, field_validator

from app.core.constants import MarketCode


class AnalysisRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    market: MarketCode
    time_horizon: str = Field(pattern="^(intraday|swing|medium_term|long_term)$")
    strategy_preference: str = Field(
        pattern="^(moving_average_crossover|rsi_oversold_rebound|breakout_n_day_high)$"
    )
    research_objective: str = Field(
        default="investment_thesis",
        min_length=1,
        max_length=80,
    )
    user_thesis: str | None = Field(default=None, max_length=1200)
    user_concerns: list[str] = Field(default_factory=list, max_length=12)
    requested_at: str | None = None
    locale: str = Field(default="en", max_length=16)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("research_objective")
    @classmethod
    def normalize_research_objective(cls, value: str) -> str:
        return value.strip() or "investment_thesis"

    @field_validator("user_thesis")
    @classmethod
    def normalize_user_thesis(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("user_concerns", mode="before")
    @classmethod
    def normalize_user_concerns_input(cls, value) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [part.strip() for part in value.splitlines() if part.strip()]
        return value

    @field_validator("locale")
    @classmethod
    def normalize_locale(cls, value: str) -> str:
        return (value or "en").strip()[:16] or "en"

    def normalized_user_concerns(self) -> list[str]:
        return [concern.strip() for concern in self.user_concerns if concern.strip()]
