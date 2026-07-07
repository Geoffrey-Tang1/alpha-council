from app.core.constants import MarketCode
from app.data_providers.ticker_normalization import normalize_yfinance_ticker


def test_yfinance_ticker_normalization_us():
    assert normalize_yfinance_ticker("nvda", MarketCode.US) == "NVDA"
    assert normalize_yfinance_ticker("AAPL", MarketCode.US) == "AAPL"


def test_yfinance_ticker_normalization_japan():
    assert normalize_yfinance_ticker("7203", MarketCode.JP) == "7203.T"
    assert normalize_yfinance_ticker("7203.T", MarketCode.JP) == "7203.T"


def test_yfinance_ticker_normalization_taiwan():
    assert normalize_yfinance_ticker("2330", MarketCode.TW) == "2330.TW"
    assert normalize_yfinance_ticker("2330.TW", MarketCode.TW) == "2330.TW"


def test_yfinance_ticker_normalization_korea():
    assert normalize_yfinance_ticker("005930", MarketCode.KR) == "005930.KS"
    assert normalize_yfinance_ticker("005930.KS", MarketCode.KR) == "005930.KS"
