from pydantic import BaseModel, Field, field_validator

from app.core.constants import DecisionAction, MarketCode


class WatchlistItemCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    market: MarketCode
    notes: str | None = None

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()


class WatchlistItemUpdate(BaseModel):
    notes: str | None = None
    latest_signal: DecisionAction | None = None
    latest_risk_level: str | None = None
    latest_price: float | None = None


class WatchlistItem(BaseModel):
    id: int
    ticker: str
    market: MarketCode
    company_name: str | None = None
    notes: str | None = None
    latest_signal: DecisionAction | None = None
    latest_risk_level: str | None = None
    latest_price: float | None = None
    created_at: str
    updated_at: str


class WatchlistResponse(BaseModel):
    items: list[WatchlistItem]
    total: int
