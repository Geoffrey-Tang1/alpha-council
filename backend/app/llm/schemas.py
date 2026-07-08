from datetime import datetime, timezone

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LLMGenerationResponse(BaseModel):
    provider: str
    model: str
    enabled: bool
    used: bool
    summary: str = ""
    reasoning_notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    prompt_name: str
    prompt_version: str
    created_at: str = Field(default_factory=utc_now_iso)


class LLMDecisionOutputs(BaseModel):
    bull_bear_summary: LLMGenerationResponse | None = None
    risk_explanation: LLMGenerationResponse | None = None
    decision_memo: LLMGenerationResponse | None = None
    research_report: LLMGenerationResponse | None = None
    prompt_versions: dict[str, str] = Field(default_factory=dict)


class LLMDecisionContext(BaseModel):
    ticker: str
    company_name: str
    display_symbol: str
    market: str
    decision: str
    confidence: float
    data_provider: str
    data_quality: str
    data_warnings: list[str]
    risk_warnings: list[str]
    invalidation_conditions: list[str]
    final_explanation: str
    entry_plan: str
    stop_loss: float | None
    take_profit: float | None
    max_position_size_pct: float
    risk_veto: bool
    risk_veto_reason: str | None
    technical_view: str
    fundamental_view: str
    news_view: str
    macro_view: str
    bull_points: list[str]
    bear_points: list[str]
    portfolio_fit: str


class LLMStatusResponse(BaseModel):
    llm_provider: str
    enabled: bool
    available: bool
    model: str | None = None
    warnings: list[str] = Field(default_factory=list)
