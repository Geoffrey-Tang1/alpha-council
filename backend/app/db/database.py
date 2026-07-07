import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from app.core.config import settings


def sqlite_path_from_url(database_url: str | None = None) -> Path:
    url = database_url or settings.database_url
    if not url.startswith("sqlite:///"):
        raise ValueError("Phase 1 supports SQLite URLs only.")

    parsed = urlparse(url)
    raw_path = parsed.path
    if raw_path.startswith("/") and not url.startswith("sqlite:////"):
        raw_path = raw_path[1:]
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def get_connection(database_url: str | None = None) -> sqlite3.Connection:
    db_path = sqlite_path_from_url(database_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_url: str | None = None) -> None:
    with get_connection(database_url) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id TEXT NOT NULL UNIQUE,
                timestamp TEXT NOT NULL,
                ticker TEXT NOT NULL,
                market TEXT NOT NULL,
                latest_price REAL,
                market_status TEXT NOT NULL,
                final_decision TEXT NOT NULL,
                confidence REAL NOT NULL,
                time_horizon TEXT NOT NULL,
                full_payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_decisions_ticker_market_timestamp
            ON decisions (ticker, market, timestamp)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_decisions_final_decision
            ON decisions (final_decision)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS watchlist_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                market TEXT NOT NULL,
                company_name TEXT,
                notes TEXT,
                latest_signal TEXT,
                latest_risk_level TEXT,
                latest_price REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(ticker, market)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_watchlist_ticker_market
            ON watchlist_items (ticker, market)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_watchlist_updated_at
            ON watchlist_items (updated_at)
            """
        )
        connection.commit()
