from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from app.backtesting.strategies import build_strategy_signals
from app.schemas.backtests import EquityCurvePoint, TradeLogEntry


HISTORICAL_SIMULATION_WARNING = "Historical simulation only. Past performance does not guarantee future results."
REQUIRED_OHLCV_COLUMNS = {"date", "open", "high", "low", "close", "volume"}
FIXED_STOP_LOSS_PCT = 0.08


class BacktestDataError(ValueError):
    pass


@dataclass(frozen=True)
class BacktestEngineResult:
    total_return: float
    cagr: float
    max_drawdown: float
    win_rate: float
    number_of_trades: int
    average_trade_return: float
    equity_curve: list[EquityCurvePoint]
    trade_log: list[TradeLogEntry]
    warning: str


class BacktestEngine:
    def run(
        self,
        history: pd.DataFrame,
        strategy_name: str,
        initial_capital: float,
        transaction_cost_bps: float,
        slippage_bps: float,
    ) -> BacktestEngineResult:
        prepared = self._prepare_history(history)
        if prepared.empty:
            return self.empty_result(
                initial_capital=initial_capital,
                extra_warning="No valid price history was available for the requested backtest period.",
            )

        signals = build_strategy_signals(prepared, strategy_name=strategy_name)
        return self._simulate(
            history=prepared,
            signals=signals,
            initial_capital=initial_capital,
            transaction_cost_bps=transaction_cost_bps,
            slippage_bps=slippage_bps,
        )

    def _prepare_history(self, history: pd.DataFrame) -> pd.DataFrame:
        if history is None or history.empty:
            return pd.DataFrame(columns=sorted(REQUIRED_OHLCV_COLUMNS))

        missing_columns = REQUIRED_OHLCV_COLUMNS.difference(history.columns)
        if missing_columns:
            raise BacktestDataError(f"Price history missing required columns: {sorted(missing_columns)}")

        prepared = history.copy()
        prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce").dt.date
        for column in ["open", "high", "low", "close", "volume"]:
            prepared[column] = pd.to_numeric(prepared[column], errors="coerce")

        prepared = prepared.dropna(subset=["date", "open", "high", "low", "close"])
        prepared = prepared.sort_values("date").drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
        return prepared

    def _simulate(
        self,
        history: pd.DataFrame,
        signals: pd.DataFrame,
        initial_capital: float,
        transaction_cost_bps: float,
        slippage_bps: float,
    ) -> BacktestEngineResult:
        transaction_cost_rate = transaction_cost_bps / 10_000
        slippage_rate = slippage_bps / 10_000
        cash = float(initial_capital)
        shares = 0.0
        pending_action: str | None = None
        pending_reason: str | None = None
        entry_state: dict | None = None
        trade_log: list[TradeLogEntry] = []
        equity_curve: list[EquityCurvePoint] = []

        for index, row in history.iterrows():
            current_date = row["date"].isoformat()
            open_price = float(row["open"])
            close_price = float(row["close"])

            if pending_action == "BUY" and shares == 0 and cash > 0:
                execution_price = open_price * (1 + slippage_rate)
                shares = cash / (execution_price * (1 + transaction_cost_rate))
                gross_cost = shares * execution_price
                transaction_cost = gross_cost * transaction_cost_rate
                entry_total_cost = gross_cost + transaction_cost
                cash -= entry_total_cost
                entry_state = {
                    "entry_date": current_date,
                    "entry_price": execution_price,
                    "entry_total_cost": entry_total_cost,
                }
            elif pending_action == "SELL" and shares > 0 and entry_state is not None:
                cash, shares = self._close_position(
                    cash=cash,
                    shares=shares,
                    exit_price=open_price * (1 - slippage_rate),
                    exit_date=current_date,
                    reason=pending_reason or "strategy_exit",
                    entry_state=entry_state,
                    transaction_cost_rate=transaction_cost_rate,
                    trade_log=trade_log,
                )
                entry_state = None

            pending_action = None
            pending_reason = None
            equity = cash + shares * close_price
            equity_curve.append(EquityCurvePoint(date=current_date, equity=round(equity, 2)))

            if index >= len(history) - 1:
                continue

            signal = signals.loc[index]
            if shares > 0 and entry_state is not None:
                stop_loss_price = entry_state["entry_price"] * (1 - FIXED_STOP_LOSS_PCT)
                if close_price <= stop_loss_price:
                    pending_action = "SELL"
                    pending_reason = "fixed_stop_loss_exit"
                elif bool(signal["exit"]):
                    pending_action = "SELL"
                    pending_reason = signal["exit_reason"] or "strategy_exit"
            elif bool(signal["entry"]):
                pending_action = "BUY"
                pending_reason = signal["entry_reason"] or "strategy_entry"

        if shares > 0 and entry_state is not None:
            last_row = history.iloc[-1]
            cash, shares = self._close_position(
                cash=cash,
                shares=shares,
                exit_price=float(last_row["close"]) * (1 - slippage_rate),
                exit_date=last_row["date"].isoformat(),
                reason="period_end_exit",
                entry_state=entry_state,
                transaction_cost_rate=transaction_cost_rate,
                trade_log=trade_log,
            )
            if equity_curve:
                equity_curve[-1] = EquityCurvePoint(date=equity_curve[-1].date, equity=round(cash, 2))

        return self._build_result(
            initial_capital=initial_capital,
            equity_curve=equity_curve,
            trade_log=trade_log,
        )

    def _close_position(
        self,
        cash: float,
        shares: float,
        exit_price: float,
        exit_date: str,
        reason: str,
        entry_state: dict,
        transaction_cost_rate: float,
        trade_log: list[TradeLogEntry],
    ) -> tuple[float, float]:
        gross_proceeds = shares * exit_price
        transaction_cost = gross_proceeds * transaction_cost_rate
        net_proceeds = gross_proceeds - transaction_cost
        cash += net_proceeds
        return_pct = net_proceeds / entry_state["entry_total_cost"] - 1
        trade_log.append(
            TradeLogEntry(
                entry_date=entry_state["entry_date"],
                entry_price=round(entry_state["entry_price"], 4),
                exit_date=exit_date,
                exit_price=round(exit_price, 4),
                return_pct=round(return_pct, 6),
                reason=reason,
            )
        )
        return cash, 0.0

    def _build_result(
        self,
        initial_capital: float,
        equity_curve: list[EquityCurvePoint],
        trade_log: list[TradeLogEntry],
    ) -> BacktestEngineResult:
        final_equity = equity_curve[-1].equity if equity_curve else initial_capital
        total_return = final_equity / initial_capital - 1
        cagr = self._calculate_cagr(initial_capital=initial_capital, final_equity=final_equity, equity_curve=equity_curve)
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        trade_returns = [trade.return_pct for trade in trade_log]
        number_of_trades = len(trade_returns)
        win_rate = sum(1 for value in trade_returns if value > 0) / number_of_trades if number_of_trades else 0
        average_trade_return = float(np.mean(trade_returns)) if trade_returns else 0

        warning = HISTORICAL_SIMULATION_WARNING
        if number_of_trades == 0:
            warning = f"{warning} No trades were generated by the selected strategy."

        return BacktestEngineResult(
            total_return=round(total_return, 6),
            cagr=round(cagr, 6),
            max_drawdown=round(max_drawdown, 6),
            win_rate=round(win_rate, 6),
            number_of_trades=number_of_trades,
            average_trade_return=round(average_trade_return, 6),
            equity_curve=equity_curve,
            trade_log=trade_log,
            warning=warning,
        )

    def empty_result(self, initial_capital: float, extra_warning: str) -> BacktestEngineResult:
        return BacktestEngineResult(
            total_return=0,
            cagr=0,
            max_drawdown=0,
            win_rate=0,
            number_of_trades=0,
            average_trade_return=0,
            equity_curve=[],
            trade_log=[],
            warning=f"{HISTORICAL_SIMULATION_WARNING} {extra_warning}",
        )

    def _calculate_cagr(
        self,
        initial_capital: float,
        final_equity: float,
        equity_curve: list[EquityCurvePoint],
    ) -> float:
        if len(equity_curve) < 2 or final_equity <= 0:
            return 0

        start = date.fromisoformat(equity_curve[0].date)
        end = date.fromisoformat(equity_curve[-1].date)
        years = (end - start).days / 365.25
        if years <= 0:
            return 0
        return (final_equity / initial_capital) ** (1 / years) - 1

    def _calculate_max_drawdown(self, equity_curve: list[EquityCurvePoint]) -> float:
        if not equity_curve:
            return 0

        values = pd.Series([point.equity for point in equity_curve], dtype="float64")
        peaks = values.cummax()
        drawdowns = values / peaks - 1
        return float(drawdowns.min())
