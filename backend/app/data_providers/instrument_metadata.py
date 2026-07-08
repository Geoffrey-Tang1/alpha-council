from app.core.constants import MarketCode
from app.data_providers.ticker_normalization import normalize_yfinance_ticker


COMMON_COMPANY_NAMES = {
    "NVDA": "NVIDIA Corporation",
    "AAPL": "Apple Inc.",
    "TSLA": "Tesla, Inc.",
    "MSFT": "Microsoft Corporation",
    "7203": "Toyota Motor Corporation",
    "7203.T": "Toyota Motor Corporation",
    "9984": "SoftBank Group Corp.",
    "9984.T": "SoftBank Group Corp.",
    "2330": "Taiwan Semiconductor Manufacturing Company Limited",
    "2330.TW": "Taiwan Semiconductor Manufacturing Company Limited",
    "005930": "Samsung Electronics Co., Ltd.",
    "005930.KS": "Samsung Electronics Co., Ltd.",
}


def _market_code(market: MarketCode | str) -> MarketCode:
    return market if isinstance(market, MarketCode) else MarketCode(str(market))


def normalize_display_symbol(ticker: str, market: MarketCode | str) -> str:
    market_code = _market_code(market)
    return normalize_yfinance_ticker(ticker=ticker, market=market_code)


def lookup_company_name(ticker: str, market: MarketCode | str) -> str:
    normalized_ticker = normalize_display_symbol(ticker=ticker, market=market)
    base_ticker = normalized_ticker.split(".", 1)[0]
    return COMMON_COMPANY_NAMES.get(normalized_ticker) or COMMON_COMPANY_NAMES.get(base_ticker) or "Unknown Company"


def build_instrument_metadata(
    ticker: str,
    market: MarketCode | str,
    company_name: str | None = None,
) -> dict[str, str]:
    normalized_ticker = normalize_display_symbol(ticker=ticker, market=market)
    clean_company_name = (company_name or "").strip()
    if (
        not clean_company_name
        or clean_company_name == "Unknown Company"
        or clean_company_name.upper() == normalized_ticker.upper()
    ):
        clean_company_name = lookup_company_name(ticker=ticker, market=market)

    return {
        "ticker": ticker.strip().upper(),
        "normalized_ticker": normalized_ticker,
        "display_symbol": normalized_ticker,
        "company_name": clean_company_name or "Unknown Company",
    }
