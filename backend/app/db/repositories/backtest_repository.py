import json

from app.data_providers.instrument_metadata import build_instrument_metadata
from app.db.database import get_connection, initialize_database
from app.schemas.backtests import BacktestResponse


class BacktestRepository:
    def __init__(self) -> None:
        initialize_database()

    def save(self, backtest: BacktestResponse) -> BacktestResponse:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO backtest_runs (
                    backtest_id,
                    ticker,
                    company_name,
                    normalized_ticker,
                    display_symbol,
                    market,
                    strategy_name,
                    start_date,
                    end_date,
                    initial_capital,
                    transaction_cost_bps,
                    slippage_bps,
                    total_return,
                    cagr,
                    max_drawdown,
                    win_rate,
                    number_of_trades,
                    average_trade_return,
                    equity_curve_json,
                    trade_log_json,
                    warning_text,
                    data_provider,
                    data_quality,
                    data_disclaimer,
                    data_warnings_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    backtest.backtest_id,
                    backtest.ticker,
                    backtest.company_name,
                    backtest.normalized_ticker,
                    backtest.display_symbol,
                    backtest.market.value,
                    backtest.strategy_name,
                    backtest.start_date.isoformat(),
                    backtest.end_date.isoformat(),
                    backtest.initial_capital,
                    backtest.transaction_cost_bps,
                    backtest.slippage_bps,
                    backtest.total_return,
                    backtest.cagr,
                    backtest.max_drawdown,
                    backtest.win_rate,
                    backtest.number_of_trades,
                    backtest.average_trade_return,
                    json.dumps([point.model_dump(mode="json") for point in backtest.equity_curve]),
                    json.dumps([trade.model_dump(mode="json") for trade in backtest.trade_log]),
                    backtest.warning,
                    backtest.data_provider,
                    backtest.data_quality,
                    backtest.data_disclaimer,
                    json.dumps(backtest.data_warnings),
                    backtest.created_at,
                ),
            )
            connection.commit()
        return backtest

    def list(self, limit: int = 100) -> list[BacktestResponse]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM backtest_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_backtest(row) for row in rows]

    def get_by_id(self, backtest_id: str) -> BacktestResponse | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM backtest_runs
                WHERE backtest_id = ?
                """,
                (backtest_id,),
            ).fetchone()

        if row is None:
            return None
        return self._row_to_backtest(row)

    def _row_to_backtest(self, row) -> BacktestResponse:
        metadata = build_instrument_metadata(
            ticker=row["ticker"],
            market=row["market"],
            company_name=row["company_name"],
        )
        return BacktestResponse(
            backtest_id=row["backtest_id"],
            ticker=row["ticker"],
            company_name=metadata["company_name"]
            if row["company_name"] in {None, "", "Unknown Company"}
            else row["company_name"],
            normalized_ticker=row["normalized_ticker"] or metadata["normalized_ticker"],
            display_symbol=row["display_symbol"] or metadata["display_symbol"],
            market=row["market"],
            strategy_name=row["strategy_name"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            initial_capital=row["initial_capital"],
            transaction_cost_bps=row["transaction_cost_bps"],
            slippage_bps=row["slippage_bps"],
            total_return=row["total_return"],
            cagr=row["cagr"],
            max_drawdown=row["max_drawdown"],
            win_rate=row["win_rate"],
            number_of_trades=row["number_of_trades"],
            average_trade_return=row["average_trade_return"],
            equity_curve=json.loads(row["equity_curve_json"]),
            trade_log=json.loads(row["trade_log_json"]),
            data_provider=row["data_provider"],
            data_quality=row["data_quality"],
            data_disclaimer=row["data_disclaimer"],
            data_warnings=json.loads(row["data_warnings_json"]),
            warning=row["warning_text"],
            created_at=row["created_at"],
        )
