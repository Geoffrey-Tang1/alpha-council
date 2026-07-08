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


class WatchlistSummaryResponse(BaseModel):
    total_items: int
    count_by_market: dict[str, int]
    count_by_latest_signal: dict[str, int]
    count_by_latest_risk_level: dict[str, int]
    high_risk_count: int
    non_real_data_count: int
    concentration_warning: str | None
    data_quality_note: str
