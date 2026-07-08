import pandas as pd

from app.backtesting.indicators import relative_strength_index, simple_moving_average


def build_strategy_signals(history: pd.DataFrame, strategy_name: str) -> pd.DataFrame:
    if strategy_name == "moving_average_crossover":
        return moving_average_crossover_signals(history)
    if strategy_name == "rsi_oversold_rebound":
        return rsi_oversold_rebound_signals(history)
    if strategy_name == "breakout_n_day_high":
        return breakout_n_day_high_signals(history)
    raise ValueError(f"Unsupported strategy: {strategy_name}")


def empty_signal_frame(history: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "entry": [False] * len(history),
            "exit": [False] * len(history),
            "entry_reason": [None] * len(history),
            "exit_reason": [None] * len(history),
        },
        index=history.index,
    )


def moving_average_crossover_signals(
    history: pd.DataFrame,
    short_window: int = 20,
    long_window: int = 50,
) -> pd.DataFrame:
    signals = empty_signal_frame(history)
    close = history["close"]
    short_ma = simple_moving_average(close, short_window)
    long_ma = simple_moving_average(close, long_window)

    previous_short = short_ma.shift(1)
    previous_long = long_ma.shift(1)
    entry = (previous_short <= previous_long) & (short_ma > long_ma)
    exit_ = (previous_short >= previous_long) & (short_ma < long_ma)

    signals.loc[entry.fillna(False), "entry"] = True
    signals.loc[entry.fillna(False), "entry_reason"] = "ma_cross_entry"
    signals.loc[exit_.fillna(False), "exit"] = True
    signals.loc[exit_.fillna(False), "exit_reason"] = "ma_cross_exit"
    return signals


def rsi_oversold_rebound_signals(
    history: pd.DataFrame,
    rsi_period: int = 14,
    oversold_threshold: float = 30,
    rebound_threshold: float = 35,
) -> pd.DataFrame:
    signals = empty_signal_frame(history)
    rsi = relative_strength_index(history["close"], period=rsi_period)

    entry = (rsi.shift(1) < oversold_threshold) & (rsi >= rebound_threshold)
    exit_ = rsi > 60

    signals.loc[entry.fillna(False), "entry"] = True
    signals.loc[entry.fillna(False), "entry_reason"] = "rsi_rebound_entry"
    signals.loc[exit_.fillna(False), "exit"] = True
    signals.loc[exit_.fillna(False), "exit_reason"] = "rsi_strength_exit"
    return signals


def breakout_n_day_high_signals(
    history: pd.DataFrame,
    breakout_window: int = 20,
) -> pd.DataFrame:
    signals = empty_signal_frame(history)
    close = history["close"]
    prior_high = history["high"].shift(1).rolling(window=breakout_window, min_periods=breakout_window).max()
    ten_day_ma = simple_moving_average(close, 10)

    entry = close > prior_high
    exit_ = close < ten_day_ma

    signals.loc[entry.fillna(False), "entry"] = True
    signals.loc[entry.fillna(False), "entry_reason"] = "breakout_entry"
    signals.loc[exit_.fillna(False), "exit"] = True
    signals.loc[exit_.fillna(False), "exit_reason"] = "breakout_ma_exit"
    return signals
