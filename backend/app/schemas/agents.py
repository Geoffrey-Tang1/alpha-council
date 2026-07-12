from pydantic import BaseModel, Field

from app.core.constants import AgentSignal, DecisionAction


class TechnicalAnalysisOutput(BaseModel):
    technical_signal: AgentSignal
    confidence: float = Field(ge=0, le=1)
    explanation: str
    key_indicators: dict[str, float | None]
    risks: list[str]


class FundamentalAnalysisOutput(BaseModel):
    fundamental_signal: AgentSignal
    confidence: float = Field(ge=0, le=1)
    explanation: str
    key_metrics: dict[str, float | str | None]
    risks: list[str]


class NewsSentimentOutput(BaseModel):
    sentiment_signal: AgentSignal
    confidence: float = Field(ge=0, le=1)
    explanation: str
    catalysts: list[str]
    risks: list[str]
    data_sources: list[str]
    provider: str = "unknown"
    article_count: int = 0
    fetched_at: str | None = None
    availability: str = "unavailable"
    freshness: str = "unknown"
    sentiment_available: bool = False
    sentiment_label: str = "unavailable"
    sentiment_method: str = "not_computed"
    source_type: str = "unavailable_source"
    unavailable_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class MacroAnalysisOutput(BaseModel):
    macro_signal: AgentSignal
    confidence: float = Field(ge=0, le=1)
    explanation: str
    macro_factors: list[str]
    risks: list[str]


class BullCaseOutput(BaseModel):
    bull_points: list[str]
    supporting_evidence: list[str]
    assumptions: list[str]
    confidence: float = Field(ge=0, le=1)


class BearCaseOutput(BaseModel):
    bear_points: list[str]
    supporting_evidence: list[str]
    risk_factors: list[str]
    confidence: float = Field(ge=0, le=1)


class RiskManagerOutput(BaseModel):
    risk_level: str
    max_position_size_pct: float = Field(ge=0)
    stop_loss_required: bool
    risk_warnings: list[str]
    veto: bool
    veto_reason: str | None
    confidence_adjustment: float


class PortfolioManagerOutput(BaseModel):
    portfolio_fit: str
    recommended_position_size_pct: float = Field(ge=0)
    concentration_warning: str | None
    explanation: str


class AgentOutputs(BaseModel):
    technical_analysis: TechnicalAnalysisOutput
    fundamental_analysis: FundamentalAnalysisOutput
    news_sentiment: NewsSentimentOutput
    macro_cross_market: MacroAnalysisOutput
    risk_manager: RiskManagerOutput
    portfolio_manager: PortfolioManagerOutput


class AgentVoteOutput(BaseModel):
    agent: str
    vote: DecisionAction
    confidence: float = Field(ge=0, le=1)
