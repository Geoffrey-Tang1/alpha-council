from datetime import datetime, timezone
from uuid import uuid4

from app.backtesting.engine import BacktestDataError, BacktestEngine, HISTORICAL_SIMULATION_WARNING
from app.core.constants import MarketCode
from app.data_providers.base import MarketDataProvider
from app.data_providers.provider_registry import get_data_provider
from app.db.repositories.backtest_repository import BacktestRepository
from app.schemas.backtests import (
    BacktestListResponse,
    BacktestResponse,
    BacktestRunRequest,
)


MINIMUM_ROWS_BY_STRATEGY = {
    "moving_average_crossover": 51,
    "rsi_oversold_rebound": 16,
    "breakout_n_day_high": 21,
}


class BacktestService:
    def __init__(
        self,
        provider: MarketDataProvider | None = None,
        repository: BacktestRepository | None = None,
        engine: BacktestEngine | None = None,
    ) -> None:
        self.provider = provider or get_data_provider()
        self.repository = repository or BacktestRepository()
        self.engine = engine or BacktestEngine()

    def run_backtest(self, payload: BacktestRunRequest) -> BacktestResponse:
        data_warnings: list[str] = []
        try:
            history = self.provider.get_price_history(
                ticker=payload.ticker,
                market=payload.market,
                start=payload.start_date,
                end=payload.end_date,
            )
            source_status = self.provider.get_data_source_status()
            data_quality = str(source_status.get("quality", "UNAVAILABLE")).upper()
            if history.empty:
                data_quality = "UNAVAILABLE"
                data_warnings.append("No historical OHLCV data was available for the requested backtest.")
            elif len(history) < MINIMUM_ROWS_BY_STRATEGY[payload.strategy_name]:
                if source_status.get("provider_name") == "yfinance" and data_quality == "REAL":
                    data_quality = "DEGRADED"
                data_warnings.append(
                    f"Only {len(history)} price rows were available; this is short for {payload.strategy_name}."
                )

            result = self.engine.run(
                history=history,
                strategy_name=payload.strategy_name,
                initial_capital=payload.initial_capital,
                transaction_cost_bps=payload.transaction_cost_bps,
                slippage_bps=payload.slippage_bps,
            )
        except BacktestDataError as exc:
            source_status = self.provider.get_data_source_status()
            data_quality = "UNAVAILABLE"
            data_warnings.append(str(exc))
            result = self.engine.empty_result(
                initial_capital=payload.initial_capital,
                extra_warning="Backtest could not run because provider data was invalid.",
            )
        except Exception as exc:  # pragma: no cover - provider-specific failures vary.
            source_status = self.provider.get_data_source_status()
            data_quality = "UNAVAILABLE"
            data_warnings.append(f"Backtest provider failure: {exc}")
            result = self.engine.empty_result(
                initial_capital=payload.initial_capital,
                extra_warning="Backtest could not run because the data provider failed.",
            )

        response = BacktestResponse(
            backtest_id=f"bt_{uuid4().hex}",
            ticker=payload.ticker,
            market=payload.market,
            strategy_name=payload.strategy_name,
            start_date=payload.start_date,
            end_date=payload.end_date,
            initial_capital=payload.initial_capital,
            transaction_cost_bps=payload.transaction_cost_bps,
            slippage_bps=payload.slippage_bps,
            total_return=result.total_return,
            cagr=result.cagr,
            max_drawdown=result.max_drawdown,
            win_rate=result.win_rate,
            number_of_trades=result.number_of_trades,
            average_trade_return=result.average_trade_return,
            equity_curve=result.equity_curve,
            trade_log=result.trade_log,
            data_provider=source_status.get("provider_name", "mock"),
            data_quality=data_quality,
            data_disclaimer=self._data_disclaimer(
                data_provider=source_status.get("provider_name", "mock"),
                data_quality=data_quality,
            ),
            data_warnings=self._data_warnings(source_status=source_status, extra_warnings=data_warnings),
            warning=result.warning if HISTORICAL_SIMULATION_WARNING in result.warning else HISTORICAL_SIMULATION_WARNING,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return self.repository.save(response)

    def list_backtests(self, limit: int = 100) -> BacktestListResponse:
        items = self.repository.list(limit=limit)
        return BacktestListResponse(items=items, total=len(items))

    def get_backtest(self, backtest_id: str) -> BacktestResponse | None:
        return self.repository.get_by_id(backtest_id)

    def _data_disclaimer(self, data_provider: str, data_quality: str) -> str:
        if data_provider == "mock" or data_quality == "MOCK":
            return "MVP Mode: using deterministic mock data. Not real market data."
        if data_provider == "yfinance" and data_quality == "REAL":
            return "Market data provided by yfinance. Data may be delayed, incomplete, or adjusted. Not financial advice."
        if data_quality == "DEGRADED":
            return "Market data provider degraded. Some data may be incomplete or fallback mock data. Not financial advice."
        return "Market data unavailable or insufficient for a reliable simulation. Not financial advice."

    def _data_warnings(self, source_status: dict, extra_warnings: list[str]) -> list[str]:
        return list(dict.fromkeys([*source_status.get("warnings", []), *extra_warnings]))
