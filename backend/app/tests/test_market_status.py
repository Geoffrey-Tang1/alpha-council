from datetime import datetime, timezone

from app.core.constants import MarketCode, MarketStatus
from app.services.market_status_service import MarketStatusService


def test_market_status_endpoint_returns_supported_markets(client):
    response = client.get("/api/v1/market-status")

    assert response.status_code == 200
    markets = response.json()["markets"]
    assert {item["market"] for item in markets} == {"US", "JP", "TW", "KR"}
    assert all(item["status"] in {"OPEN", "CLOSED", "UNKNOWN"} for item in markets)
    assert all("TODO" in " ".join(item["notes"]) for item in markets)


def test_us_market_open_during_regular_session():
    service = MarketStatusService()
    # 2026-07-07 14:00 UTC is 10:00 in New York during regular trading hours.
    status = service.get_market_status(
        market=MarketCode.US,
        now_utc=datetime(2026, 7, 7, 14, 0, tzinfo=timezone.utc),
    )

    assert status.status == MarketStatus.OPEN
