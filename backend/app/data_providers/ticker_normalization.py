from app.core.constants import MarketCode


YFINANCE_SUFFIXES = {
    MarketCode.JP: ".T",
    MarketCode.TW: ".TW",
    MarketCode.KR: ".KS",
}


def normalize_yfinance_ticker(ticker: str, market: MarketCode) -> str:
    clean = ticker.strip().upper()
    if market == MarketCode.US:
        return clean

    suffix = YFINANCE_SUFFIXES.get(market)
    if suffix is None:
        return clean

    if clean.endswith(suffix):
        return clean

    base = clean.split(".", 1)[0]
    return f"{base}{suffix}"
