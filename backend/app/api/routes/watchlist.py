from fastapi import APIRouter, HTTPException

from app.schemas.watchlist import (
    WatchlistItem,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistResponse,
    WatchlistSummaryResponse,
)
from app.services.watchlist_service import WatchlistService

router = APIRouter(prefix="/watchlist", tags=["watchlist"])
service = WatchlistService()


@router.get("", response_model=WatchlistResponse)
def list_watchlist() -> WatchlistResponse:
    return service.list_items()


@router.post("", response_model=WatchlistItem, status_code=201)
def create_watchlist_item(payload: WatchlistItemCreate) -> WatchlistItem:
    try:
        return service.create_item(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/summary", response_model=WatchlistSummaryResponse)
def watchlist_summary() -> WatchlistSummaryResponse:
    return service.summary()


@router.get("/{item_id}", response_model=WatchlistItem)
def get_watchlist_item(item_id: int) -> WatchlistItem:
    item = service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found.")
    return item


@router.patch("/{item_id}", response_model=WatchlistItem)
def update_watchlist_item(item_id: int, payload: WatchlistItemUpdate) -> WatchlistItem:
    item = service.update_item(item_id=item_id, payload=payload)
    if item is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found.")
    return item


@router.delete("/{item_id}", status_code=204)
def delete_watchlist_item(item_id: int) -> None:
    deleted = service.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Watchlist item not found.")
