from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.constants import MarketCode


SUPPORTED_BACKTEST_STRATEGIES = {
    "moving_average_crossover",
    "rsi_oversold_rebound",
    "breakout_n_day_high",
}


class BacktestRunRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    market: MarketCode
    start_date: date
    end_date: date
    strategy_name: str
    initial_capital: float = Field(gt=0)
    transaction_cost_bps: float = Field(default=5, ge=0, le=500)
    slippage_bps: float = Field(default=10, ge=0, le=500)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("strategy_name")
    @classmethod
    def validate_strategy(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SUPPORTED_BACKTEST_STRATEGIES:
            raise ValueError("Unsupported backtest strategy.")
        return normalized

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date.")
        return self


class EquityCurvePoint(BaseModel):
    date: str
    equity: float


class TradeLogEntry(BaseModel):
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    return_pct: float
    reason: str


class BacktestResponse(BaseModel):
    backtest_id: str
    ticker: str
    market: MarketCode
    strategy_name: str
    start_date: date
    end_date: date
    initial_capital: float
    transaction_cost_bps: float
    slippage_bps: float
    total_return: float
    cagr: float
    max_drawdown: float
    win_rate: float
    number_of_trades: int
    average_trade_return: float
    equity_curve: list[EquityCurvePoint]
    trade_log: list[TradeLogEntry]
    data_provider: str
    data_quality: str
    data_disclaimer: str
    data_warnings: list[str]
    warning: str
    created_at: str


class BacktestListResponse(BaseModel):
    items: list[BacktestResponse]
    total: int
