import numpy as np
import pandas as pd


def simple_moving_average(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def relative_strength_index(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    average_gain = gain.rolling(window=period, min_periods=period).mean()
    average_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = average_gain / average_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.where(average_loss != 0, 100)
    return rsi.fillna(50)
