from pydantic import BaseModel, Field, field_validator

from app.core.constants import MarketCode


class AnalysisRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    market: MarketCode
    time_horizon: str = Field(pattern="^(intraday|swing|medium_term|long_term)$")
    strategy_preference: str = Field(
        pattern="^(moving_average_crossover|rsi_oversold_rebound|breakout_n_day_high)$"
    )

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()
