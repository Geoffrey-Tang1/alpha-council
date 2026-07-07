from enum import StrEnum


class MarketCode(StrEnum):
    US = "US"
    JP = "JP"
    TW = "TW"
    KR = "KR"


class MarketStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


class DecisionAction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WATCH = "WATCH"
    AVOID = "AVOID"


class AgentSignal(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WATCH = "WATCH"
    AVOID = "AVOID"


SUPPORTED_MARKETS = {
    MarketCode.US: {
        "display_name": "United States",
        "timezone": "America/New_York",
        "regular_open": "09:30",
        "regular_close": "16:00",
    },
    MarketCode.JP: {
        "display_name": "Japan",
        "timezone": "Asia/Tokyo",
        "regular_open": "09:00",
        "regular_close": "15:30",
    },
    MarketCode.TW: {
        "display_name": "Taiwan",
        "timezone": "Asia/Taipei",
        "regular_open": "09:00",
        "regular_close": "13:30",
    },
    MarketCode.KR: {
        "display_name": "Korea",
        "timezone": "Asia/Seoul",
        "regular_open": "09:00",
        "regular_close": "15:30",
    },
}

MARKET_STATUS_TODO_NOTES = [
    "MVP uses hardcoded regular sessions.",
    "TODO: public holidays, half-days, lunch breaks, exact exchange calendars, and daylight saving edge cases.",
]
