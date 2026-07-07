from pydantic import BaseModel

from app.core.constants import MarketCode, MarketStatus


class MarketSession(BaseModel):
    regular_open: str
    regular_close: str


class MarketStatusItem(BaseModel):
    market: MarketCode
    display_name: str
    timezone: str
    status: MarketStatus
    local_time: str
    session: MarketSession
    notes: list[str]


class MarketStatusResponse(BaseModel):
    markets: list[MarketStatusItem]
