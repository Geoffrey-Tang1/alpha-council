from datetime import datetime, timezone
import sqlite3

from app.db.database import get_connection, initialize_database
from app.schemas.watchlist import WatchlistItem, WatchlistItemCreate, WatchlistItemUpdate


class WatchlistRepository:
    def __init__(self) -> None:
        initialize_database()

    def create(self, payload: WatchlistItemCreate) -> WatchlistItem:
        now = datetime.now(timezone.utc).isoformat()
        try:
            with get_connection() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO watchlist_items (
                        ticker,
                        market,
                        notes,
                        latest_signal,
                        latest_risk_level,
                        latest_price,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload.ticker,
                        payload.market.value,
                        payload.notes,
                        "WATCH",
                        "UNKNOWN",
                        None,
                        now,
                        now,
                    ),
                )
                connection.commit()
                item_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise ValueError("Watchlist item already exists for ticker and market.") from exc

        item = self.get(item_id)
        if item is None:
            raise RuntimeError("Created watchlist item could not be loaded.")
        return item

    def list(self) -> list[WatchlistItem]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM watchlist_items
                ORDER BY updated_at DESC, ticker ASC
                """
            ).fetchall()

        return [self._row_to_item(row) for row in rows]

    def get(self, item_id: int) -> WatchlistItem | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM watchlist_items
                WHERE id = ?
                """,
                (item_id,),
            ).fetchone()

        if row is None:
            return None
        return self._row_to_item(row)

    def update(self, item_id: int, payload: WatchlistItemUpdate) -> WatchlistItem | None:
        existing = self.get(item_id)
        if existing is None:
            return None

        values = payload.model_dump(exclude_unset=True, mode="json")
        if not values:
            return existing

        values["updated_at"] = datetime.now(timezone.utc).isoformat()
        assignments = ", ".join(f"{column} = ?" for column in values)
        params = [*values.values(), item_id]

        with get_connection() as connection:
            connection.execute(
                f"""
                UPDATE watchlist_items
                SET {assignments}
                WHERE id = ?
                """,
                params,
            )
            connection.commit()

        return self.get(item_id)

    def delete(self, item_id: int) -> bool:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                DELETE FROM watchlist_items
                WHERE id = ?
                """,
                (item_id,),
            )
            connection.commit()
            return cursor.rowcount > 0

    def _row_to_item(self, row) -> WatchlistItem:
        return WatchlistItem(
            id=row["id"],
            ticker=row["ticker"],
            market=row["market"],
            company_name=row["company_name"],
            notes=row["notes"],
            latest_signal=row["latest_signal"],
            latest_risk_level=row["latest_risk_level"],
            latest_price=row["latest_price"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
