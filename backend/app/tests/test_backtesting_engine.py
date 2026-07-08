from datetime import date

import pandas as pd

from app.backtesting.engine import HISTORICAL_SIMULATION_WARNING, BacktestEngine
from app.backtesting.strategies import (
    breakout_n_day_high_signals,
    moving_average_crossover_signals,
    rsi_oversold_rebound_signals,
)
from app.core.constants import MarketCode
from app.data_providers.yfinance_provider import YFinanceDataProvider
from app.schemas.backtests import BacktestRunRequest
from app.services.backtest_service import BacktestService


def make_history(closes: list[float], start: str = "2023-01-02") -> pd.DataFrame:
    dates = pd.bdate_range(start=start, periods=len(closes))
    return pd.DataFrame(
        {
            "date": dates.date.astype(str),
            "open": closes,
            "high": [value * 1.01 for value in closes],
            "low": [value * 0.99 for value in closes],
            "close": closes,
            "volume": [1_000_000] * len(closes),
        }
    )


def test_moving_average_crossover_generates_next_bar_trade():
    history = make_history([100] * 55 + list(range(101, 141)) + list(range(140, 90, -1)))
    signals = moving_average_crossover_signals(history)
    first_signal_index = int(signals.index[signals["entry"]][0])

    result = BacktestEngine().run(
        history=history,
        strategy_name="moving_average_crossover",
        initial_capital=100_000,
        transaction_cost_bps=0,
        slippage_bps=0,
    )

    assert result.number_of_trades >= 1
    assert result.trade_log[0].entry_date == history.loc[first_signal_index + 1, "date"]


def test_rsi_oversold_rebound_strategy_generates_trade():
    history = make_history(
        list(range(100, 78, -1))
        + [79, 80, 82, 85, 88, 91, 94, 97, 100]
        + list(range(101, 116))
    )

    signals = rsi_oversold_rebound_signals(history)
    result = BacktestEngine().run(
        history=history,
        strategy_name="rsi_oversold_rebound",
        initial_capital=100_000,
        transaction_cost_bps=0,
        slippage_bps=0,
    )

    assert signals["entry"].any()
    assert result.number_of_trades >= 1
    assert result.trade_log[0].reason in {"rsi_strength_exit", "period_end_exit", "fixed_stop_loss_exit"}


def test_breakout_n_day_high_uses_prior_high_and_generates_trade():
    history = make_history([100] * 25 + [106, 108, 110, 112, 114, 109, 105, 101, 99, 98])
    signals = breakout_n_day_high_signals(history)

    assert bool(signals.loc[25, "entry"]) is True
    assert bool(signals.loc[20, "entry"]) is False

    result = BacktestEngine().run(
        history=history,
        strategy_name="breakout_n_day_high",
        initial_capital=100_000,
        transaction_cost_bps=0,
        slippage_bps=0,
    )

    assert result.number_of_trades >= 1


def test_metrics_and_no_trade_case_are_returned():
    history = make_history([100] * 80)
    result = BacktestEngine().run(
        history=history,
        strategy_name="moving_average_crossover",
        initial_capital=100_000,
        transaction_cost_bps=5,
        slippage_bps=10,
    )

    assert result.number_of_trades == 0
    assert result.win_rate == 0
    assert result.average_trade_return == 0
    assert result.total_return == 0
    assert result.equity_curve
    assert "No trades were generated" in result.warning
    assert HISTORICAL_SIMULATION_WARNING in result.warning


def test_backtest_service_uses_mock_provider_mode():
    request = BacktestRunRequest(
        ticker="NVDA",
        market=MarketCode.US,
        start_date=date(2023, 1, 1),
        end_date=date(2024, 12, 31),
        strategy_name="moving_average_crossover",
        initial_capital=100_000,
        transaction_cost_bps=5,
        slippage_bps=10,
    )

    result = BacktestService().run_backtest(request)

    assert result.backtest_id.startswith("bt_")
    assert result.data_provider == "mock"
    assert result.data_quality == "MOCK"
    assert result.equity_curve
    assert HISTORICAL_SIMULATION_WARNING in result.warning


class FakeYFinanceModule:
    def Ticker(self, symbol):
        return FakeTicker(symbol)


class FakeTicker:
    def __init__(self, symbol):
        self.symbol = symbol
        self.fast_info = {}
        self.info = {}
        self.news = []

    def history(self, **kwargs):
        closes = [100] * 25 + list(range(101, 151)) + list(range(150, 115, -1))
        dates = pd.date_range("2023-01-02", periods=len(closes), freq="B")
        return pd.DataFrame(
            {
                "Open": closes,
                "High": [value * 1.01 for value in closes],
                "Low": [value * 0.99 for value in closes],
                "Close": closes,
                "Volume": [1_000_000] * len(closes),
            },
            index=dates[: len(closes)],
        )


def test_backtest_service_supports_yfinance_with_mocked_yfinance_module():
    provider = YFinanceDataProvider(yf_module=FakeYFinanceModule())
    request = BacktestRunRequest(
        ticker="NVDA",
        market=MarketCode.US,
        start_date=date(2023, 1, 1),
        end_date=date(2024, 12, 31),
        strategy_name="breakout_n_day_high",
        initial_capital=100_000,
        transaction_cost_bps=5,
        slippage_bps=10,
    )

    result = BacktestService(provider=provider).run_backtest(request)

    assert result.data_provider == "yfinance"
    assert result.data_quality == "REAL"
    assert result.equity_curve
    assert HISTORICAL_SIMULATION_WARNING in result.warning
