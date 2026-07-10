from datetime import datetime, timezone
from enum import StrEnum

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


class LLMProviderName(StrEnum):
    DISABLED = "disabled"
    MOCK = "mock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    XAI = "xai"
    MISTRAL = "mistral"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    CUSTOM_OPENAI_COMPATIBLE = "custom_openai_compatible"


class LLMSettingsResponse(BaseModel):
    llm_provider: LLMProviderName
    enable_llm_reasoning: bool
    selected_model: str
    api_key_present: bool
    masked_api_key: str | None = None
    base_url: str | None = None
    temperature: float = Field(ge=0, le=2)
    max_tokens: int = Field(ge=128, le=8000)
    timeout_seconds: int = Field(ge=5, le=120)
    available_models: list[str]
    last_connection_status: str
    last_connection_message: str
    updated_at: str


class LLMSettingsUpdate(BaseModel):
    llm_provider: LLMProviderName | None = None
    enable_llm_reasoning: bool | None = None
    selected_model: str | None = Field(default=None, min_length=1, max_length=160)
    api_key: str | None = Field(default=None, max_length=4096)
    base_url: str | None = Field(default=None, max_length=512)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=128, le=8000)
    timeout_seconds: int | None = Field(default=None, ge=5, le=120)


class LLMConnectionTestRequest(BaseModel):
    llm_provider: LLMProviderName
    selected_model: str | None = Field(default=None, max_length=160)
    api_key: str | None = Field(default=None, max_length=4096)
    base_url: str | None = Field(default=None, max_length=512)


class LLMConnectionTestResponse(BaseModel):
    success: bool
    provider: LLMProviderName
    model: str
    message: str
    latency_ms: int


class LLMModelInfo(BaseModel):
    id: str
    name: str
    source: str
    created: int | str | None = None
    metadata: dict = Field(default_factory=dict)


class LLMModelCatalogResponse(BaseModel):
    provider: LLMProviderName
    models: list[LLMModelInfo]
    source: str
    fetched_at: str | None = None
    status: str
    message: str
    supports_refresh: bool


class LLMModelRefreshRequest(BaseModel):
    provider: LLMProviderName
