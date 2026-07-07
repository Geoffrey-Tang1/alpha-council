from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.constants import MARKET_STATUS_TODO_NOTES, SUPPORTED_MARKETS, MarketCode, MarketStatus
from app.core.timezones import parse_session_time
from app.schemas.market import MarketSession, MarketStatusItem, MarketStatusResponse


class MarketStatusService:
    def get_all_market_statuses(self, now_utc: datetime | None = None) -> MarketStatusResponse:
        return MarketStatusResponse(
            markets=[
                self.get_market_status(market=market, now_utc=now_utc)
                for market in (MarketCode.US, MarketCode.JP, MarketCode.TW, MarketCode.KR)
            ]
        )

    def get_market_status(
        self,
        market: MarketCode,
        now_utc: datetime | None = None,
    ) -> MarketStatusItem:
        config = SUPPORTED_MARKETS.get(market)
        if config is None:
            return MarketStatusItem(
                market=market,
                display_name="Unknown",
                timezone="Unknown",
                status=MarketStatus.UNKNOWN,
                local_time="",
                session=MarketSession(regular_open="", regular_close=""),
                notes=["Unknown market code."],
            )

        timezone = ZoneInfo(config["timezone"])
        reference_time = now_utc or datetime.now(tz=ZoneInfo("UTC"))
        local_time = reference_time.astimezone(timezone)

        regular_open = parse_session_time(config["regular_open"])
        regular_close = parse_session_time(config["regular_close"])
        is_weekday = local_time.weekday() < 5
        is_regular_session = regular_open <= local_time.time() < regular_close
        status = MarketStatus.OPEN if is_weekday and is_regular_session else MarketStatus.CLOSED

        return MarketStatusItem(
            market=market,
            display_name=config["display_name"],
            timezone=config["timezone"],
            status=status,
            local_time=local_time.isoformat(),
            session=MarketSession(
                regular_open=config["regular_open"],
                regular_close=config["regular_close"],
            ),
            notes=MARKET_STATUS_TODO_NOTES,
        )
