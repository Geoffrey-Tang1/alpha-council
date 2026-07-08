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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS backtest_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id TEXT NOT NULL UNIQUE,
                ticker TEXT NOT NULL,
                market TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                initial_capital REAL NOT NULL,
                transaction_cost_bps REAL NOT NULL,
                slippage_bps REAL NOT NULL,
                total_return REAL NOT NULL,
                cagr REAL NOT NULL,
                max_drawdown REAL NOT NULL,
                win_rate REAL NOT NULL,
                number_of_trades INTEGER NOT NULL,
                average_trade_return REAL NOT NULL,
                equity_curve_json TEXT NOT NULL,
                trade_log_json TEXT NOT NULL,
                warning_text TEXT NOT NULL,
                data_provider TEXT NOT NULL,
                data_quality TEXT NOT NULL,
                data_disclaimer TEXT NOT NULL,
                data_warnings_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_backtest_runs_ticker_market_created
            ON backtest_runs (ticker, market, created_at)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_backtest_runs_strategy
            ON backtest_runs (strategy_name)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS decision_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluation_id TEXT NOT NULL UNIQUE,
                decision_id TEXT NOT NULL,
                ticker TEXT NOT NULL,
                market TEXT NOT NULL,
                decision TEXT NOT NULL,
                confidence REAL NOT NULL,
                decision_timestamp TEXT NOT NULL,
                decision_price REAL,
                evaluation_status TEXT NOT NULL,
                forward_return_1d REAL,
                forward_return_5d REAL,
                forward_return_20d REAL,
                forward_return_60d REAL,
                max_drawdown_20d REAL,
                max_drawdown_60d REAL,
                max_runup_20d REAL,
                max_runup_60d REAL,
                directional_result TEXT NOT NULL,
                evaluation_summary TEXT NOT NULL,
                data_provider TEXT NOT NULL,
                data_quality TEXT NOT NULL,
                data_disclaimer TEXT NOT NULL,
                data_warnings_json TEXT NOT NULL,
                full_payload_json TEXT NOT NULL,
                evaluated_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_decision_evaluations_decision_id
            ON decision_evaluations (decision_id)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_decision_evaluations_ticker_market
            ON decision_evaluations (ticker, market)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_decision_evaluations_decision
            ON decision_evaluations (decision)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_decision_evaluations_directional_result
            ON decision_evaluations (directional_result)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_decision_evaluations_confidence
            ON decision_evaluations (confidence)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_decision_evaluations_evaluated_at
            ON decision_evaluations (evaluated_at)
            """
        )
        connection.commit()
