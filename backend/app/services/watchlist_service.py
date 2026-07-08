from app.db.repositories.watchlist_repository import WatchlistRepository
from app.schemas.watchlist import (
    WatchlistItem,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistResponse,
    WatchlistSummaryResponse,
)


class WatchlistService:
    def __init__(self, repository: WatchlistRepository | None = None) -> None:
        self.repository = repository or WatchlistRepository()

    def create_item(self, payload: WatchlistItemCreate) -> WatchlistItem:
        return self.repository.create(payload)

    def list_items(self) -> WatchlistResponse:
        items = self.repository.list()
        return WatchlistResponse(items=items, total=len(items))

    def summary(self) -> WatchlistSummaryResponse:
        items = self.repository.list()
        count_by_market = self._count(items, lambda item: item.market.value)
        count_by_signal = self._count(items, lambda item: item.latest_signal.value if item.latest_signal else "UNKNOWN")
        count_by_risk = self._count(items, lambda item: (item.latest_risk_level or "UNKNOWN").upper())
        high_risk_count = sum(
            (item.latest_risk_level or "UNKNOWN").upper() in {"HIGH", "EXTREME"} for item in items
        )
        concentration_warning = self._concentration_warning(count_by_market=count_by_market, total=len(items))

        return WatchlistSummaryResponse(
            total_items=len(items),
            count_by_market=count_by_market,
            count_by_latest_signal=count_by_signal,
            count_by_latest_risk_level=count_by_risk,
            high_risk_count=high_risk_count,
            non_real_data_count=0,
            concentration_warning=concentration_warning,
            data_quality_note="Watchlist items do not yet persist per-item provider quality; decision and evaluation views show data_quality explicitly.",
        )

    def get_item(self, item_id: int) -> WatchlistItem | None:
        return self.repository.get(item_id)

    def update_item(self, item_id: int, payload: WatchlistItemUpdate) -> WatchlistItem | None:
        return self.repository.update(item_id=item_id, payload=payload)

    def delete_item(self, item_id: int) -> bool:
        return self.repository.delete(item_id)

    def _count(self, items: list[WatchlistItem], key_fn) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            key = key_fn(item)
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _concentration_warning(self, count_by_market: dict[str, int], total: int) -> str | None:
        if total == 0:
            return None
        dominant_market, dominant_count = max(count_by_market.items(), key=lambda item: item[1])
        if dominant_count / total > 0.6:
            return f"{dominant_market} represents more than 60% of the watchlist."
        return None
