from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    cached_at: datetime
    ttl_seconds: int

    @property
    def is_fresh(self) -> bool:
        return datetime.now(timezone.utc) - self.cached_at <= timedelta(seconds=self.ttl_seconds)


class FinancialDataCache:
    """Small in-process cache for local MVP provider calls.

    This cache is intentionally backend-local and never includes API keys in keys
    or values. It is suitable for development, not distributed deployments.
    """

    def __init__(self) -> None:
        self._store: dict[tuple, CacheEntry] = {}

    def get(self, key: tuple) -> CacheEntry | None:
        return self._store.get(key)

    def set(self, key: tuple, value: Any, ttl_seconds: int) -> None:
        self._store[key] = CacheEntry(
            value=value,
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=ttl_seconds,
        )

    def clear(self) -> None:
        self._store.clear()

    def stats(self) -> dict[str, int]:
        fresh = sum(1 for entry in self._store.values() if entry.is_fresh)
        return {
            "entries": len(self._store),
            "fresh_entries": fresh,
            "stale_entries": len(self._store) - fresh,
        }


GLOBAL_FINANCIAL_DATA_CACHE = FinancialDataCache()

