from pydantic import BaseModel, Field

from app.core.constants import DecisionAction, MarketCode, MarketStatus
from app.schemas.agents import AgentOutputs, AgentVoteOutput, BearCaseOutput, BullCaseOutput
from app.schemas.common import DataSource


class DecisionResponse(BaseModel):
    decision_id: str
    ticker: str
    company_name: str = "Unknown Company"
    normalized_ticker: str = ""
    display_symbol: str = ""
    market: MarketCode
    latest_price: float | None
    market_status: MarketStatus
    decision: DecisionAction
    confidence: float = Field(ge=0, le=1)
    time_horizon: str
    entry_plan: str
    stop_loss: float | None
    take_profit: float | None
    max_position_size_pct: float
    bull_case: BullCaseOutput
    bear_case: BearCaseOutput
    risk_warnings: list[str]
    invalidation_conditions: list[str]
    agent_votes: list[AgentVoteOutput]
    agent_outputs: AgentOutputs
    final_explanation: str
    data_sources: list[DataSource]
    data_provider: str
    data_quality: str
    data_disclaimer: str
    data_warnings: list[str]
    timestamp: str
    saved: bool


class DecisionSummary(BaseModel):
    decision_id: str
    timestamp: str
    ticker: str
    company_name: str = "Unknown Company"
    normalized_ticker: str = ""
    display_symbol: str = ""
    market: MarketCode
    decision: DecisionAction
    confidence: float = Field(ge=0, le=1)
    latest_price: float | None
    market_status: MarketStatus
    final_explanation: str


class DecisionListResponse(BaseModel):
    items: list[DecisionResponse]
    total: int
