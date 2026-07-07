from app.db.repositories.watchlist_repository import WatchlistRepository
from app.schemas.watchlist import WatchlistItem, WatchlistItemCreate, WatchlistItemUpdate, WatchlistResponse


class WatchlistService:
    def __init__(self, repository: WatchlistRepository | None = None) -> None:
        self.repository = repository or WatchlistRepository()

    def create_item(self, payload: WatchlistItemCreate) -> WatchlistItem:
        return self.repository.create(payload)

    def list_items(self) -> WatchlistResponse:
        items = self.repository.list()
        return WatchlistResponse(items=items, total=len(items))

    def get_item(self, item_id: int) -> WatchlistItem | None:
        return self.repository.get(item_id)

    def update_item(self, item_id: int, payload: WatchlistItemUpdate) -> WatchlistItem | None:
        return self.repository.update(item_id=item_id, payload=payload)

    def delete_item(self, item_id: int) -> bool:
        return self.repository.delete(item_id)
