from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.constants import DecisionAction, MarketCode


RESEARCH_SCHEMA_VERSION = "research_report_v1"


class ResearchDimensionStatus(StrEnum):
    AVAILABLE = "available"
    PARTIALLY_AVAILABLE = "partially_available"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"
    FAILED = "failed"


class EvidenceSourceType(StrEnum):
    INTERNAL_CALCULATION = "internal_calculation"
    EXISTING_MARKET_DATA_SERVICE = "existing_market_data_service"
    EXISTING_APPLICATION_DATA = "existing_application_data"
    USER_PROVIDED_CONTEXT = "user_provided_context"
    MODEL_INFERENCE = "model_inference"
    MOCK_DATA = "mock_data"
    UNAVAILABLE_SOURCE = "unavailable_source"


class EvidenceKind(StrEnum):
    FACTUAL_DATA = "factual_data"
    USER_INPUT = "user_input"
    MODEL_INFERENCE = "model_inference"
    DERIVED_CALCULATION = "derived_calculation"
    UNAVAILABLE_INFORMATION = "unavailable_information"


class EvidenceAvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class FreshnessStatus(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"
    UNKNOWN = "unknown"


class ResearchRequestMetadata(BaseModel):
    ticker: str
    market: MarketCode
    strategy: str
    investment_horizon: str
    research_objective: str
    user_thesis: str | None = None
    user_concerns: list[str] = Field(default_factory=list)
    requested_at: str
    llm_provider: str
    llm_model: str | None = None
    reasoning_enabled: bool
    locale: str = "en"


class ResearchPlanDimension(BaseModel):
    name: str
    status: ResearchDimensionStatus
    description: str
    required: bool = True
    available_sources: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ResearchPlan(BaseModel):
    plan_id: str
    dimensions: list[ResearchPlanDimension]
    limitations: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    evidence_id: str
    category: str
    title: str
    summary: str
    value: str | float | int | bool | None = None
    source_type: EvidenceSourceType
    source_name: str
    source_reference: str | None = None
    observed_at: str
    period_start: str | None = None
    period_end: str | None = None
    freshness_status: FreshnessStatus
    confidence: float = Field(ge=0, le=1)
    availability_status: EvidenceAvailabilityStatus
    error_or_limitation: str | None = None
    evidence_kind: EvidenceKind


class SpecialistResearchOutput(BaseModel):
    module_name: str
    status: ResearchDimensionStatus
    conclusion: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    opposing_evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class ResearchCase(BaseModel):
    core_argument: str
    supporting_factors: list[str] = Field(default_factory=list)
    required_assumptions: list[str] = Field(default_factory=list)
    possible_catalysts: list[str] = Field(default_factory=list)
    invalidation_conditions: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    information_gaps: list[str] = Field(default_factory=list)


class ResearchRiskItem(BaseModel):
    risk_id: str
    category: str
    description: str
    severity: RiskSeverity
    likelihood: RiskSeverity
    evidence_ids: list[str] = Field(default_factory=list)
    mitigation_or_monitoring: str
    uncertainty: str
    status: str


class StructuredRiskReview(BaseModel):
    overall_risk_level: str
    veto: bool
    veto_reason: str | None = None
    risks: list[ResearchRiskItem] = Field(default_factory=list)
    data_quality_risks: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ConfidenceAssessment(BaseModel):
    level: ConfidenceLevel
    score: float = Field(ge=0, le=1)
    methodology: str
    contributing_factors: list[str] = Field(default_factory=list)
    confidence_penalties: list[str] = Field(default_factory=list)
    unresolved_uncertainty: list[str] = Field(default_factory=list)


class DataQualitySummary(BaseModel):
    overall_completeness: str
    unavailable_dimensions: list[str] = Field(default_factory=list)
    stale_evidence_count: int = 0
    failed_modules: list[str] = Field(default_factory=list)
    inference_heavy_sections: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CommitteeResearchDecision(BaseModel):
    decision: DecisionAction
    decision_rationale: str
    supporting_module_decisions: list[str] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)
    dominant_risks: list[str] = Field(default_factory=list)
    confidence: ConfidenceAssessment
    conditions_required_for_upgrade: list[str] = Field(default_factory=list)
    conditions_requiring_downgrade: list[str] = Field(default_factory=list)
    monitoring_checklist: list[str] = Field(default_factory=list)


class InvestmentThesis(BaseModel):
    thesis_statement: str
    executive_summary: str
    bull_case: ResearchCase
    bear_case: ResearchCase
    neutral_case: str | None = None
    key_assumptions: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    valuation_view: SpecialistResearchOutput
    technical_view: SpecialistResearchOutput
    macro_view: SpecialistResearchOutput
    time_horizon: str
    thesis_breakers: list[str] = Field(default_factory=list)
    monitoring_conditions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    evidence_coverage: str
    confidence: ConfidenceAssessment
    recommendation: DecisionAction
    recommendation_limitations: list[str] = Field(default_factory=list)


class ResearchStageStatus(BaseModel):
    stage: str
    status: str
    message: str


class StructuredResearchReport(BaseModel):
    schema_version: str = RESEARCH_SCHEMA_VERSION
    report_id: str
    request: ResearchRequestMetadata
    execution_status: str
    stage_statuses: list[ResearchStageStatus]
    research_plan: ResearchPlan
    evidence: list[EvidenceItem]
    specialist_outputs: list[SpecialistResearchOutput]
    investment_thesis: InvestmentThesis
    risk_review: StructuredRiskReview
    confidence_assessment: ConfidenceAssessment
    committee_decision: CommitteeResearchDecision
    data_quality_summary: DataQualitySummary
    missing_information: list[str]
    source_attribution_note: str
    method_and_limitations: list[str]
    warnings: list[str] = Field(default_factory=list)
    created_at: str
    provider_metadata: dict[str, str | bool | None] = Field(default_factory=dict)
