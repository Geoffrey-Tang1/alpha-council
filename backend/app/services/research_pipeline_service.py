from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd

from app.core.constants import DecisionAction
from app.financial_data.schemas import (
    DataAvailability as FinancialDataAvailability,
    DataFreshness as FinancialDataFreshness,
    DataSourceMetadata,
    FinancialDataSnapshot,
    FinancialMetric,
)
from app.llm.settings_store import get_llm_settings_response
from app.schemas.agents import (
    BearCaseOutput,
    BullCaseOutput,
    FundamentalAnalysisOutput,
    MacroAnalysisOutput,
    NewsSentimentOutput,
    PortfolioManagerOutput,
    RiskManagerOutput,
    TechnicalAnalysisOutput,
)
from app.schemas.analysis import AnalysisRequest
from app.schemas.decisions import DecisionResponse
from app.schemas.research import (
    CommitteeResearchDecision,
    ConfidenceAssessment,
    ConfidenceLevel,
    DataQualitySummary,
    EvidenceAvailabilityStatus,
    EvidenceItem,
    EvidenceKind,
    EvidenceSourceType,
    FreshnessStatus,
    InvestmentThesis,
    RESEARCH_SCHEMA_VERSION,
    ResearchCase,
    ResearchDimensionStatus,
    ResearchPlan,
    ResearchPlanDimension,
    ResearchRequestMetadata,
    ResearchRiskItem,
    ResearchStageStatus,
    RiskSeverity,
    SpecialistResearchOutput,
    StructuredResearchReport,
    StructuredRiskReview,
)


class ResearchPipelineService:
    """Build a structured research record from the deterministic analysis workflow."""

    def build_report(
        self,
        *,
        request: AnalysisRequest,
        collected_data: dict,
        technical: TechnicalAnalysisOutput,
        fundamental: FundamentalAnalysisOutput,
        news: NewsSentimentOutput,
        macro: MacroAnalysisOutput,
        bull_case: BullCaseOutput,
        bear_case: BearCaseOutput,
        risk: RiskManagerOutput,
        portfolio: PortfolioManagerOutput,
        decision: DecisionResponse,
    ) -> StructuredResearchReport:
        created_at = datetime.now(timezone.utc).isoformat()
        report_id = f"research_{uuid4().hex[:12]}"
        llm_settings = get_llm_settings_response()
        request_metadata = ResearchRequestMetadata(
            ticker=request.ticker,
            market=request.market,
            strategy=request.strategy_preference,
            investment_horizon=request.time_horizon,
            research_objective=request.research_objective,
            user_thesis=request.user_thesis,
            user_concerns=request.normalized_user_concerns(),
            requested_at=request.requested_at or created_at,
            llm_provider=str(llm_settings.llm_provider),
            llm_model=llm_settings.selected_model,
            reasoning_enabled=llm_settings.enable_llm_reasoning,
            locale=request.locale or "en",
        )

        evidence = self._build_evidence(
            request=request,
            collected_data=collected_data,
            technical=technical,
            fundamental=fundamental,
            news=news,
            macro=macro,
            decision=decision,
            created_at=created_at,
        )
        plan = self._build_plan(collected_data, technical, fundamental, news, macro, evidence)
        missing_information = self._missing_information(plan, evidence)
        specialist_outputs = self._build_specialist_outputs(
            technical=technical,
            fundamental=fundamental,
            news=news,
            macro=macro,
            risk=risk,
            evidence=evidence,
        )
        risk_review = self._build_risk_review(risk, portfolio, decision, evidence, missing_information)
        data_quality_summary = self._build_data_quality_summary(plan, specialist_outputs, evidence, decision)
        confidence = self._build_confidence(plan, specialist_outputs, evidence, decision, data_quality_summary)
        thesis = self._build_thesis(
            decision=decision,
            request=request,
            bull_case=bull_case,
            bear_case=bear_case,
            news=news,
            specialist_outputs=specialist_outputs,
            risk_review=risk_review,
            confidence=confidence,
            missing_information=missing_information,
        )
        committee = self._build_committee_decision(
            decision=decision,
            specialist_outputs=specialist_outputs,
            risk_review=risk_review,
            confidence=confidence,
        )
        stage_statuses = self._stage_statuses(plan, specialist_outputs, missing_information)

        return StructuredResearchReport(
            schema_version=RESEARCH_SCHEMA_VERSION,
            report_id=report_id,
            request=request_metadata,
            execution_status="partial_success" if missing_information else "completed",
            stage_statuses=stage_statuses,
            research_plan=plan,
            evidence=evidence,
            specialist_outputs=specialist_outputs,
            investment_thesis=thesis,
            risk_review=risk_review,
            confidence_assessment=confidence,
            committee_decision=committee,
            data_quality_summary=data_quality_summary,
            missing_information=missing_information,
            source_attribution_note=(
                "Evidence items label whether they come from connected market data, deterministic "
                "internal calculations, user context, mock data, model inference, or unavailable sources. "
                "Model inference is not treated as external market data."
            ),
            method_and_limitations=[
                "Wisoka Compass generates research support only, not personalized financial advice.",
                "No live trading, order routing, broker execution, or portfolio execution is implemented.",
                "The selected strategy is recorded as research context; Phase 7 does not run strategy execution inside stock analysis.",
                "Unavailable sources are surfaced explicitly rather than fabricated.",
            ],
            warnings=list(dict.fromkeys([*decision.data_warnings, *risk.risk_warnings])),
            created_at=created_at,
            provider_metadata={
                "data_provider": decision.data_provider,
                "data_quality": decision.data_quality,
                "financial_data_provider": financial_data.provider if (financial_data := self._financial_snapshot(collected_data)) else None,
                "financial_data_availability": financial_data.availability_status if financial_data else None,
                "financial_data_freshness": financial_data.freshness_status if financial_data else None,
                "llm_provider": decision.llm_provider,
                "llm_model": decision.llm_model,
                "llm_used": decision.llm_used,
            },
        )

    def _build_evidence(
        self,
        *,
        request: AnalysisRequest,
        collected_data: dict,
        technical: TechnicalAnalysisOutput,
        fundamental: FundamentalAnalysisOutput,
        news: NewsSentimentOutput,
        macro: MacroAnalysisOutput,
        decision: DecisionResponse,
        created_at: str,
    ) -> list[EvidenceItem]:
        source_type = self._provider_source_type(decision.data_provider, decision.data_quality)
        source_name = decision.data_provider or "unknown"
        history: pd.DataFrame = collected_data.get("price_history", pd.DataFrame())
        financial_data = self._financial_snapshot(collected_data)
        quote = financial_data.quote if financial_data else None
        evidence: list[EvidenceItem] = [
            self._evidence(
                "ev_latest_price",
                "market_data",
                "Latest price",
                f"Latest available price for {decision.display_symbol or decision.ticker}.",
                decision.latest_price,
                self._provider_source_type(financial_data.provider, decision.data_quality) if financial_data else source_type,
                quote.source.provider if quote else source_name,
                quote.observed_at or created_at if quote else created_at,
                EvidenceKind.FACTUAL_DATA,
                EvidenceAvailabilityStatus.AVAILABLE if decision.latest_price is not None else EvidenceAvailabilityStatus.UNAVAILABLE,
                confidence=0.85 if decision.latest_price is not None else 0.0,
                limitation=None if decision.latest_price is not None else "Latest price is missing.",
                source_metadata=quote.source if quote else None,
                freshness=self._freshness_from_financial(quote.freshness_status) if quote else None,
            ),
            self._evidence(
                "ev_market_status",
                "market_context",
                "Market status",
                f"Market status at analysis time was {decision.market_status}.",
                str(decision.market_status),
                EvidenceSourceType.EXISTING_APPLICATION_DATA,
                "market_status_service",
                created_at,
                EvidenceKind.FACTUAL_DATA,
                EvidenceAvailabilityStatus.AVAILABLE,
                confidence=0.75,
                limitation="Market calendars are simplified and do not include all holidays or half-days.",
            ),
        ]

        if financial_data:
            evidence.extend(self._financial_evidence(financial_data, created_at))

        if not history.empty:
            evidence.append(
                self._evidence(
                    "ev_price_history",
                    "market_data",
                    "Price history",
                    f"Historical OHLCV rows available: {len(history)}.",
                    len(history),
                    source_type,
                    source_name,
                    created_at,
                    EvidenceKind.FACTUAL_DATA,
                    EvidenceAvailabilityStatus.AVAILABLE if len(history) >= 60 else EvidenceAvailabilityStatus.PARTIAL,
                    confidence=0.8 if len(history) >= 60 else 0.45,
                    limitation=None if len(history) >= 60 else "Price history is short for medium-term confirmation.",
                    source_metadata=financial_data.price_history.source if financial_data else None,
                    freshness=self._freshness_from_financial(financial_data.price_history.freshness_status) if financial_data else None,
                )
            )
        else:
            evidence.append(
                self._unavailable_evidence(
                    "ev_price_history",
                    "market_data",
                    "Price history",
                    "Historical price data is unavailable.",
                    created_at,
                )
            )

        for key, value in technical.key_indicators.items():
            evidence.append(
                self._evidence(
                    f"ev_technical_{key}",
                    "technical",
                    key,
                    f"Derived technical indicator: {key}.",
                    value,
                    EvidenceSourceType.INTERNAL_CALCULATION,
                    "technical_analysis_agent",
                    created_at,
                    EvidenceKind.DERIVED_CALCULATION,
                    EvidenceAvailabilityStatus.AVAILABLE if value is not None else EvidenceAvailabilityStatus.PARTIAL,
                    confidence=technical.confidence if value is not None else 0.25,
                    limitation=None if value is not None else f"{key} could not be calculated from available history.",
                )
            )

        normalized_financial_keys = self._normalized_financial_keys(financial_data)
        for key, value in fundamental.key_metrics.items():
            if key in normalized_financial_keys or key in {"availability_status", "freshness_status"}:
                continue
            evidence.append(
                self._evidence(
                    f"ev_fundamental_{key}",
                    "fundamental",
                    key,
                    f"Simplified fundamental metric: {key}.",
                    self._stringify_value(value),
                    source_type if decision.data_quality != "MOCK" else EvidenceSourceType.MOCK_DATA,
                    source_name,
                    created_at,
                    EvidenceKind.FACTUAL_DATA,
                    EvidenceAvailabilityStatus.AVAILABLE if value not in {None, ""} else EvidenceAvailabilityStatus.PARTIAL,
                    confidence=fundamental.confidence if value not in {None, ""} else 0.25,
                    limitation="Fundamental coverage is simplified and may be incomplete.",
                )
            )

        for index, catalyst in enumerate(news.catalysts, start=1):
            evidence.append(
                self._evidence(
                    f"ev_catalyst_{index}",
                    "catalyst",
                    f"Catalyst {index}",
                    catalyst,
                    catalyst,
                    EvidenceSourceType.MOCK_DATA if decision.data_quality == "MOCK" else EvidenceSourceType.MODEL_INFERENCE,
                    "news_sentiment_agent",
                    created_at,
                    EvidenceKind.MODEL_INFERENCE,
                    EvidenceAvailabilityStatus.PARTIAL,
                    confidence=news.confidence,
                    limitation="Catalyst detection is placeholder logic; no dedicated news API is connected.",
                )
            )

        for index, factor in enumerate(macro.macro_factors, start=1):
            evidence.append(
                self._evidence(
                    f"ev_macro_{index}",
                    "macro",
                    f"Macro factor {index}",
                    factor,
                    factor,
                    EvidenceSourceType.INTERNAL_CALCULATION,
                    "macro_cross_market_agent",
                    created_at,
                    EvidenceKind.MODEL_INFERENCE,
                    EvidenceAvailabilityStatus.PARTIAL,
                    confidence=macro.confidence,
                    limitation="Macro view is placeholder logic; no external macro feed is connected.",
                )
            )

        if request.user_thesis:
            evidence.append(
                self._evidence(
                    "ev_user_thesis",
                    "user_context",
                    "User thesis",
                    request.user_thesis,
                    request.user_thesis,
                    EvidenceSourceType.USER_PROVIDED_CONTEXT,
                    "user",
                    created_at,
                    EvidenceKind.USER_INPUT,
                    EvidenceAvailabilityStatus.AVAILABLE,
                    confidence=0.5,
                    limitation="User-provided context is not independently verified by Wisoka Compass.",
                )
            )
        for index, concern in enumerate(request.normalized_user_concerns(), start=1):
            evidence.append(
                self._evidence(
                    f"ev_user_concern_{index}",
                    "user_context",
                    f"User concern {index}",
                    concern,
                    concern,
                    EvidenceSourceType.USER_PROVIDED_CONTEXT,
                    "user",
                    created_at,
                    EvidenceKind.USER_INPUT,
                    EvidenceAvailabilityStatus.AVAILABLE,
                    confidence=0.5,
                    limitation="User-provided concern is not independently verified by Wisoka Compass.",
                )
            )

        if decision.llm_used:
            llm_outputs = decision.llm_outputs
            llm_items = [
                ("bull_bear_summary", llm_outputs.bull_bear_summary),
                ("risk_explanation", llm_outputs.risk_explanation),
                ("decision_memo", llm_outputs.decision_memo),
                ("research_report", llm_outputs.research_report),
            ]
            for name, output in llm_items:
                if output is None or not output.summary:
                    continue
                evidence.append(
                    self._evidence(
                        f"ev_llm_{name}",
                        "model_reasoning",
                        name,
                        output.summary,
                        output.summary,
                        EvidenceSourceType.MODEL_INFERENCE,
                        output.provider,
                        created_at,
                        EvidenceKind.MODEL_INFERENCE,
                        EvidenceAvailabilityStatus.PARTIAL,
                        confidence=0.4,
                        limitation="LLM-generated content is a reasoning aid and is not an external data source.",
                    )
                )

        unavailable_sources = [
            ("ev_unavailable_filing", "fundamental", "Latest filing", "Latest company filing is not connected in this MVP."),
            ("ev_unavailable_valuation_model", "valuation", "Full valuation model", "Full valuation model inputs are unavailable."),
            ("ev_unavailable_news_feed", "catalyst", "Verified news feed", "Dedicated verified news and announcements feed is unavailable."),
            ("ev_unavailable_macro_feed", "macro", "External macro feed", "Rates, FX, sector rotation, and macro calendar feeds are unavailable."),
        ]
        for evidence_id, category, title, summary in unavailable_sources:
            evidence.append(self._unavailable_evidence(evidence_id, category, title, summary, created_at))

        return evidence

    def _financial_evidence(self, financial_data: FinancialDataSnapshot, created_at: str) -> list[EvidenceItem]:
        evidence: list[EvidenceItem] = []
        profile = financial_data.company_profile
        if profile.availability_status != FinancialDataAvailability.UNAVAILABLE:
            profile_bits = [
                profile.display_name,
                profile.sector,
                profile.industry,
                profile.exchange,
                profile.currency,
            ]
            evidence.append(
                self._evidence(
                    "ev_instrument_profile",
                    "instrument_overview",
                    "Instrument profile",
                    "Basic company and exchange metadata normalized from the active provider.",
                    " · ".join(str(bit) for bit in profile_bits if bit),
                    self._provider_source_type(financial_data.provider, "MOCK" if financial_data.provider == "mock" else "REAL"),
                    profile.source.provider,
                    profile.source.observed_at or created_at,
                    EvidenceKind.FACTUAL_DATA,
                    self._availability_from_financial(profile.availability_status),
                    confidence=profile.confidence,
                    limitation=None if profile.availability_status == FinancialDataAvailability.AVAILABLE else "Company profile is incomplete.",
                    source_metadata=profile.source,
                    freshness=self._freshness_from_financial(profile.freshness_status),
                )
            )
        if financial_data.price_history.bars:
            bars = financial_data.price_history.bars
            if len(bars) >= 2 and bars[0].close and bars[-1].close:
                evidence.append(
                    self._evidence(
                        "ev_price_return_available_window",
                        "technical",
                        "Available-window price return",
                        f"Price return across the available daily history window ({bars[0].date} to {bars[-1].date}).",
                        round((bars[-1].close / bars[0].close) - 1, 6),
                        EvidenceSourceType.INTERNAL_CALCULATION,
                        "financial_data_service",
                        bars[-1].date,
                        EvidenceKind.DERIVED_CALCULATION,
                        EvidenceAvailabilityStatus.AVAILABLE,
                        confidence=0.75,
                        limitation="This is a historical calculation over available rows, not a forecast.",
                        source_metadata=financial_data.price_history.source,
                        freshness=self._freshness_from_financial(financial_data.price_history.freshness_status),
                        formula="last_close / first_close - 1",
                    )
                )
            drawdown = self._max_drawdown_from_bars(bars)
            if drawdown is not None:
                evidence.append(
                    self._evidence(
                        "ev_price_max_drawdown_available_window",
                        "technical",
                        "Available-window max drawdown",
                        "Maximum close-to-close drawdown calculated from available daily history.",
                        drawdown,
                        EvidenceSourceType.INTERNAL_CALCULATION,
                        "financial_data_service",
                        bars[-1].date,
                        EvidenceKind.DERIVED_CALCULATION,
                        EvidenceAvailabilityStatus.AVAILABLE,
                        confidence=0.72,
                        limitation="Drawdown is calculated from available close prices only.",
                        source_metadata=financial_data.price_history.source,
                        freshness=self._freshness_from_financial(financial_data.price_history.freshness_status),
                        formula="min(close / rolling_peak - 1)",
                    )
                )
        for metric in financial_data.financial_metrics.metrics:
            evidence.append(self._metric_evidence(metric, "fundamental", "ev_financial", created_at))
        for metric in financial_data.valuation_metrics.metrics:
            evidence.append(self._metric_evidence(metric, "valuation", "ev_valuation", created_at))
        if financial_data.financial_statements.availability_status == FinancialDataAvailability.UNAVAILABLE:
            evidence.append(
                self._evidence(
                    "ev_financial_statements_unavailable",
                    "fundamental",
                    "Full financial statements",
                    "Full statement history is not available through the current financial-data adapter.",
                    None,
                    EvidenceSourceType.UNAVAILABLE_SOURCE,
                    "not_connected",
                    created_at,
                    EvidenceKind.UNAVAILABLE_INFORMATION,
                    EvidenceAvailabilityStatus.UNAVAILABLE,
                    confidence=0,
                    limitation="Income statement, balance sheet, and cash-flow statement history are unavailable.",
                    source_metadata=financial_data.financial_statements.source,
                    freshness=FreshnessStatus.UNAVAILABLE,
                )
            )
        return evidence

    def _metric_evidence(
        self,
        metric: FinancialMetric,
        category: str,
        prefix: str,
        created_at: str,
    ) -> EvidenceItem:
        title = metric.name.replace("_", " ")
        period = metric.period.period_end or metric.source.period_end
        summary = f"{title} was normalized from {metric.source.provider}."
        if metric.reported_or_derived == "derived" and metric.formula:
            summary = f"{title} was derived using {metric.formula}."
        return self._evidence(
            f"{prefix}_{metric.name}",
            category,
            title,
            summary,
            metric.value,
            EvidenceSourceType.INTERNAL_CALCULATION if metric.reported_or_derived == "derived" else self._source_type_from_metadata(metric.source),
            metric.source.provider,
            metric.source.observed_at or period or created_at,
            EvidenceKind.DERIVED_CALCULATION if metric.reported_or_derived == "derived" else EvidenceKind.FACTUAL_DATA,
            self._availability_from_financial(metric.availability_status),
            confidence=0.68 if metric.reported_or_derived == "reported" else 0.58,
            limitation=None if metric.value is not None else "Metric value is unavailable.",
            source_metadata=metric.source,
            freshness=self._freshness_from_financial(metric.source.period_end and FinancialDataFreshness.CURRENT or FinancialDataFreshness.UNKNOWN),
            formula=metric.formula,
            period_end=period,
        )

    def _build_plan(
        self,
        collected_data: dict,
        technical: TechnicalAnalysisOutput,
        fundamental: FundamentalAnalysisOutput,
        news: NewsSentimentOutput,
        macro: MacroAnalysisOutput,
        evidence: list[EvidenceItem],
    ) -> ResearchPlan:
        history: pd.DataFrame = collected_data.get("price_history", pd.DataFrame())
        fundamentals = collected_data.get("fundamentals", {})
        company_profile = collected_data.get("company_profile", {})
        financial_data = self._financial_snapshot(collected_data)
        news_is_placeholder = "placeholder" in news.explanation.lower() or "mock" in news.explanation.lower()
        macro_is_placeholder = "placeholder" in " ".join([macro.explanation, *macro.risks]).lower()
        profile_status = (
            self._dimension_status_from_financial(financial_data.company_profile.availability_status)
            if financial_data
            else ResearchDimensionStatus.AVAILABLE if company_profile else ResearchDimensionStatus.PARTIALLY_AVAILABLE
        )
        fundamentals_status = (
            self._dimension_status_from_financial(financial_data.financial_metrics.availability_status)
            if financial_data
            else ResearchDimensionStatus.PARTIALLY_AVAILABLE if fundamentals else ResearchDimensionStatus.UNAVAILABLE
        )
        valuation_status = (
            self._dimension_status_from_financial(financial_data.valuation_metrics.availability_status)
            if financial_data
            else ResearchDimensionStatus.PARTIALLY_AVAILABLE
            if any(key in fundamentals for key in ["forward_pe", "trailing_pe", "price_to_sales"])
            else ResearchDimensionStatus.UNAVAILABLE
        )
        technical_status = (
            self._dimension_status_from_financial(financial_data.price_history.availability_status)
            if financial_data
            else ResearchDimensionStatus.AVAILABLE if len(history) >= 60 else ResearchDimensionStatus.PARTIALLY_AVAILABLE
        )
        return ResearchPlan(
            plan_id=f"plan_{uuid4().hex[:10]}",
            dimensions=[
                ResearchPlanDimension(
                    name="market_context",
                    status=ResearchDimensionStatus.AVAILABLE,
                    description="Market status and supported market metadata are available.",
                    available_sources=["market_status_service"],
                    limitations=["Exchange holiday and half-day rules remain simplified."],
                ),
                ResearchPlanDimension(
                    name="company_or_instrument_overview",
                    status=profile_status,
                    description="Company profile metadata is normalized from the active financial data provider when available.",
                    available_sources=["financial_data.company_profile"] if company_profile else [],
                    limitations=[] if profile_status == ResearchDimensionStatus.AVAILABLE else ["Company profile is incomplete or unavailable."],
                ),
                ResearchPlanDimension(
                    name="fundamentals",
                    status=fundamentals_status,
                    description="Basic normalized financial metrics are available only when the active provider returns usable values.",
                    available_sources=["financial_data.financial_metrics"] if fundamentals_status != ResearchDimensionStatus.UNAVAILABLE else [],
                    limitations=[*fundamental.risks, *self._snapshot_warnings(financial_data, "financial_metrics")],
                ),
                ResearchPlanDimension(
                    name="valuation",
                    status=valuation_status,
                    description="Provider-reported or transparently derived valuation metrics are used when available.",
                    available_sources=["financial_data.valuation_metrics"] if valuation_status != ResearchDimensionStatus.UNAVAILABLE else [],
                    limitations=[
                        "No DCF, comparable-company set, segment model, or analyst estimates are connected.",
                        *self._snapshot_warnings(financial_data, "valuation_metrics"),
                    ],
                ),
                ResearchPlanDimension(
                    name="price_and_technical_behavior",
                    status=technical_status,
                    description="Technical indicators are calculated from available OHLCV history.",
                    available_sources=["financial_data.price_history", "technical_analysis_agent"] if not history.empty else [],
                    limitations=technical.risks,
                ),
                ResearchPlanDimension(
                    name="macro_sensitivity",
                    status=ResearchDimensionStatus.PARTIALLY_AVAILABLE if macro_is_placeholder else ResearchDimensionStatus.AVAILABLE,
                    description="Macro view is currently a deterministic placeholder, not a connected macro-data workflow.",
                    available_sources=["macro_cross_market_agent"],
                    limitations=macro.risks,
                ),
                ResearchPlanDimension(
                    name="catalysts",
                    status=ResearchDimensionStatus.PARTIALLY_AVAILABLE if news_is_placeholder else ResearchDimensionStatus.AVAILABLE,
                    description="Catalysts are surfaced from available news/sentiment placeholders or provider metadata.",
                    available_sources=news.data_sources,
                    limitations=news.risks,
                ),
                ResearchPlanDimension(
                    name="risks",
                    status=ResearchDimensionStatus.AVAILABLE,
                    description="Risk review is available through deterministic risk controls.",
                    available_sources=["risk_manager_agent"],
                    limitations=["Risk manager is rule-based and does not validate a real portfolio."],
                ),
                ResearchPlanDimension(
                    name="competing_interpretations",
                    status=ResearchDimensionStatus.AVAILABLE,
                    description="Bull and bear cases are constructed separately from available agent evidence.",
                    available_sources=["bull_case_agent", "bear_case_agent"],
                    limitations=["Cases are limited by available evidence coverage."],
                ),
                ResearchPlanDimension(
                    name="missing_information",
                    status=ResearchDimensionStatus.AVAILABLE,
                    description="Unavailable dimensions are listed explicitly.",
                    available_sources=[item.evidence_id for item in evidence if item.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE],
                    limitations=[],
                ),
            ],
            limitations=[
                "No dedicated filings, news, macro, or broker data source is connected in this phase.",
                "The report is a research artifact and does not execute or guarantee trades.",
            ],
        )

    def _build_specialist_outputs(
        self,
        *,
        technical: TechnicalAnalysisOutput,
        fundamental: FundamentalAnalysisOutput,
        news: NewsSentimentOutput,
        macro: MacroAnalysisOutput,
        risk: RiskManagerOutput,
        evidence: list[EvidenceItem],
    ) -> list[SpecialistResearchOutput]:
        valuation_items = [item for item in evidence if item.category == "valuation"]
        valuation_ids = [item.evidence_id for item in valuation_items]
        fundamental_ids = self._ids_by_category(evidence, "fundamental")
        technical_ids = self._ids_by_category(evidence, "technical")
        catalyst_ids = self._ids_by_category(evidence, "catalyst")
        macro_ids = self._ids_by_category(evidence, "macro")
        return [
            SpecialistResearchOutput(
                module_name="fundamental_analysis",
                status=ResearchDimensionStatus.AVAILABLE
                if any(item.availability_status == EvidenceAvailabilityStatus.AVAILABLE for item in evidence if item.category == "fundamental")
                else ResearchDimensionStatus.UNAVAILABLE,
                conclusion=fundamental.explanation,
                supporting_evidence_ids=fundamental_ids,
                assumptions=["Provider metrics are treated as a normalized snapshot with explicit provenance."],
                limitations=fundamental.risks + ["Full filing-level financial statement history is not connected."],
                missing_inputs=["Full income statement", "Cash-flow statement", "Balance sheet details"],
                confidence=fundamental.confidence,
            ),
            SpecialistResearchOutput(
                module_name="valuation_analysis",
                status=ResearchDimensionStatus.AVAILABLE
                if any(item.availability_status == EvidenceAvailabilityStatus.AVAILABLE for item in valuation_items)
                else ResearchDimensionStatus.UNAVAILABLE,
                conclusion="Valuation view is limited to available provider-reported or transparently derived metrics; no target price is generated.",
                supporting_evidence_ids=valuation_ids,
                assumptions=["Simple valuation ratios are not sufficient for a complete valuation conclusion."],
                limitations=["DCF, scenario analysis, peer multiples, and estimate revisions are unavailable."],
                missing_inputs=["Comparable company set", "Forward estimates", "Discount-rate assumptions", "Segment-level forecasts"],
                confidence=0.5 if valuation_ids else 0.15,
            ),
            SpecialistResearchOutput(
                module_name="technical_analysis",
                status=ResearchDimensionStatus.AVAILABLE if technical.key_indicators else ResearchDimensionStatus.UNAVAILABLE,
                conclusion=technical.explanation,
                supporting_evidence_ids=technical_ids,
                assumptions=["Indicators are derived from available close-price history without future leakage."],
                limitations=technical.risks,
                missing_inputs=[] if technical.key_indicators else ["Usable price history"],
                confidence=technical.confidence,
            ),
            SpecialistResearchOutput(
                module_name="macro_analysis",
                status=ResearchDimensionStatus.PARTIALLY_AVAILABLE,
                conclusion=macro.explanation,
                supporting_evidence_ids=macro_ids,
                assumptions=["Macro context is a deterministic placeholder until a real macro provider is connected."],
                limitations=macro.risks,
                missing_inputs=["Rates data", "FX data", "Sector rotation data", "Macro calendar"],
                confidence=macro.confidence,
            ),
            SpecialistResearchOutput(
                module_name="catalyst_analysis",
                status=ResearchDimensionStatus.PARTIALLY_AVAILABLE,
                conclusion=news.explanation,
                supporting_evidence_ids=catalyst_ids,
                assumptions=["Catalysts are treated as placeholders unless a real news item is present."],
                limitations=news.risks,
                missing_inputs=["Verified news feed", "Earnings calendar", "Analyst revision feed"],
                confidence=news.confidence,
            ),
            SpecialistResearchOutput(
                module_name="risk_analysis",
                status=ResearchDimensionStatus.AVAILABLE,
                conclusion=risk.veto_reason or "Risk review completed with deterministic MVP controls.",
                supporting_evidence_ids=["ev_latest_price", "ev_price_history"],
                assumptions=["No live portfolio positions or broker account data are connected."],
                limitations=risk.risk_warnings,
                missing_inputs=["Real portfolio exposure", "Liquidity depth", "Upcoming event calendar"],
                confidence=max(0.1, min(0.9, 0.65 + risk.confidence_adjustment)),
            ),
        ]

    def _build_risk_review(
        self,
        risk: RiskManagerOutput,
        portfolio: PortfolioManagerOutput,
        decision: DecisionResponse,
        evidence: list[EvidenceItem],
        missing_information: list[str],
    ) -> StructuredRiskReview:
        risk_items = [
            ResearchRiskItem(
                risk_id="risk_data_quality",
                category="data-quality risk",
                description=f"Data quality is {decision.data_quality}; warnings must be considered before acting.",
                severity=self._severity_from_quality(decision.data_quality),
                likelihood=RiskSeverity.HIGH if decision.data_quality != "REAL" else RiskSeverity.MEDIUM,
                evidence_ids=["ev_latest_price", "ev_price_history"],
                mitigation_or_monitoring="Use connected, verified data before upgrading confidence or position sizing.",
                uncertainty="High when data is mock, degraded, unavailable, stale, or incomplete.",
                status="active",
            ),
            ResearchRiskItem(
                risk_id="risk_market",
                category="market risk",
                description="Price trends, volatility, and broad market conditions can invalidate the thesis.",
                severity=RiskSeverity.MEDIUM if risk.risk_level in {"LOW", "MEDIUM"} else RiskSeverity.HIGH,
                likelihood=RiskSeverity.MEDIUM,
                evidence_ids=["ev_price_history"],
                mitigation_or_monitoring="Monitor technical trend, volatility, and invalidation conditions.",
                uncertainty="Macro and sector data are only partially available.",
                status="active",
            ),
            ResearchRiskItem(
                risk_id="risk_thesis",
                category="thesis risk",
                description="The thesis depends on incomplete fundamentals, placeholder catalysts, and unavailable filings/news.",
                severity=RiskSeverity.HIGH if missing_information else RiskSeverity.MEDIUM,
                likelihood=RiskSeverity.MEDIUM,
                evidence_ids=[item.evidence_id for item in evidence if item.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE],
                mitigation_or_monitoring="Resolve missing information before treating the thesis as high conviction.",
                uncertainty="Material because multiple research dimensions are incomplete.",
                status="active" if missing_information else "watch",
            ),
            ResearchRiskItem(
                risk_id="risk_portfolio_fit",
                category="portfolio risk",
                description=portfolio.explanation,
                severity=RiskSeverity.HIGH if risk.veto else RiskSeverity.MEDIUM,
                likelihood=RiskSeverity.MEDIUM,
                evidence_ids=[],
                mitigation_or_monitoring=portfolio.concentration_warning or "Keep position sizing within risk limits.",
                uncertainty="No real portfolio or account exposure data is connected.",
                status="blocked" if risk.veto else "active",
            ),
        ]
        return StructuredRiskReview(
            overall_risk_level=risk.risk_level,
            veto=risk.veto,
            veto_reason=risk.veto_reason,
            risks=risk_items,
            data_quality_risks=decision.data_warnings,
            limitations=["Risk review is deterministic and cannot validate live liquidity, event risk, or account exposure."],
        )

    def _build_data_quality_summary(
        self,
        plan: ResearchPlan,
        specialists: list[SpecialistResearchOutput],
        evidence: list[EvidenceItem],
        decision: DecisionResponse,
    ) -> DataQualitySummary:
        unavailable_dimensions = [
            dimension.name
            for dimension in plan.dimensions
            if dimension.status in {ResearchDimensionStatus.UNAVAILABLE, ResearchDimensionStatus.FAILED}
        ]
        partial_dimensions = [
            dimension.name
            for dimension in plan.dimensions
            if dimension.status == ResearchDimensionStatus.PARTIALLY_AVAILABLE
        ]
        failed_modules = [
            output.module_name
            for output in specialists
            if output.status == ResearchDimensionStatus.FAILED
        ]
        inference_sections = sorted(
            {
                item.category
                for item in evidence
                if item.evidence_kind == EvidenceKind.MODEL_INFERENCE
                or item.source_type == EvidenceSourceType.MODEL_INFERENCE
            }
        )
        if unavailable_dimensions:
            completeness = "limited"
        elif partial_dimensions or decision.data_quality != "REAL":
            completeness = "partial"
        else:
            completeness = "broad"
        return DataQualitySummary(
            overall_completeness=completeness,
            unavailable_dimensions=unavailable_dimensions,
            stale_evidence_count=sum(1 for item in evidence if item.freshness_status == FreshnessStatus.STALE),
            failed_modules=failed_modules,
            inference_heavy_sections=inference_sections,
            warnings=list(dict.fromkeys([decision.data_disclaimer, *decision.data_warnings])),
        )

    def _build_confidence(
        self,
        plan: ResearchPlan,
        specialists: list[SpecialistResearchOutput],
        evidence: list[EvidenceItem],
        decision: DecisionResponse,
        data_quality_summary: DataQualitySummary,
    ) -> ConfidenceAssessment:
        score = 0.72
        penalties: list[str] = []
        unavailable_count = len(data_quality_summary.unavailable_dimensions)
        partial_count = sum(1 for dimension in plan.dimensions if dimension.status == ResearchDimensionStatus.PARTIALLY_AVAILABLE)
        failed_count = len(data_quality_summary.failed_modules)
        inference_count = sum(1 for item in evidence if item.evidence_kind == EvidenceKind.MODEL_INFERENCE)

        if decision.data_quality == "MOCK":
            score -= 0.25
            penalties.append("Mock data materially limits confidence.")
        elif decision.data_quality == "DEGRADED":
            score -= 0.2
            penalties.append("Degraded provider data reduces confidence.")
        elif decision.data_quality == "UNAVAILABLE":
            score -= 0.4
            penalties.append("Unavailable market data prevents a confident conclusion.")

        if unavailable_count:
            score -= min(0.25, unavailable_count * 0.07)
            penalties.append(f"{unavailable_count} research dimension(s) are unavailable.")
        if partial_count:
            score -= min(0.18, partial_count * 0.03)
            penalties.append(f"{partial_count} research dimension(s) are only partially available.")
        if failed_count:
            score -= min(0.2, failed_count * 0.08)
            penalties.append(f"{failed_count} specialist module(s) failed.")
        if inference_count:
            score -= min(0.15, inference_count * 0.02)
            penalties.append("Some sections depend on model or placeholder inference.")

        specialist_confidence = sum(output.confidence for output in specialists) / max(len(specialists), 1)
        score = (score * 0.7) + (specialist_confidence * 0.3)
        score = round(max(0.05, min(0.9, score)), 2)
        if score < 0.4:
            level = ConfidenceLevel.LOW
        elif score < 0.7:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.HIGH
        return ConfidenceAssessment(
            level=level,
            score=score,
            methodology=(
                "Score starts from a medium evidence baseline, then applies penalties for unavailable dimensions, "
                "partial modules, data-quality issues, failed modules, and inference-heavy sections. It is rounded "
                "to avoid false precision."
            ),
            contributing_factors=[
                f"{len(evidence)} evidence item(s) normalized.",
                f"Average specialist confidence: {round(specialist_confidence, 2)}.",
                f"Committee confidence before research penalties: {round(decision.confidence, 2)}.",
            ],
            confidence_penalties=list(dict.fromkeys(penalties)),
            unresolved_uncertainty=[
                "No dedicated filings, verified news feed, macro feed, or real portfolio exposure is connected.",
                "Confidence does not imply probability of profit or future performance.",
            ],
        )

    def _build_thesis(
        self,
        *,
        decision: DecisionResponse,
        request: AnalysisRequest,
        bull_case: BullCaseOutput,
        bear_case: BearCaseOutput,
        news: NewsSentimentOutput,
        specialist_outputs: list[SpecialistResearchOutput],
        risk_review: StructuredRiskReview,
        confidence: ConfidenceAssessment,
        missing_information: list[str],
    ) -> InvestmentThesis:
        technical_view = self._find_output(specialist_outputs, "technical_analysis")
        valuation_view = self._find_output(specialist_outputs, "valuation_analysis")
        macro_view = self._find_output(specialist_outputs, "macro_analysis")
        bull = ResearchCase(
            core_argument=bull_case.bull_points[0] if bull_case.bull_points else "Bull case is limited by available evidence.",
            supporting_factors=bull_case.bull_points,
            required_assumptions=bull_case.assumptions,
            possible_catalysts=news.catalysts,
            invalidation_conditions=decision.invalidation_conditions,
            evidence_references=self._case_evidence_refs("bull", specialist_outputs),
            confidence=bull_case.confidence,
            information_gaps=missing_information,
        )
        bear = ResearchCase(
            core_argument=bear_case.bear_points[0] if bear_case.bear_points else "Bear case is limited by available evidence.",
            supporting_factors=bear_case.bear_points,
            required_assumptions=["Risk controls and missing information should be resolved before higher-conviction action."],
            possible_catalysts=["Negative price confirmation", "Unfavorable data-quality update", *news.risks],
            invalidation_conditions=["Improved verified data coverage", "Risk veto clears", *decision.invalidation_conditions],
            evidence_references=self._case_evidence_refs("bear", specialist_outputs),
            confidence=bear_case.confidence,
            information_gaps=missing_information,
        )
        return InvestmentThesis(
            thesis_statement=(
                f"{decision.company_name} ({decision.display_symbol or decision.ticker}) receives a "
                f"{decision.decision} committee decision because the available evidence is limited, risk-controlled, "
                "and subject to data-quality constraints."
            ),
            executive_summary=decision.final_explanation,
            bull_case=bull,
            bear_case=bear,
            neutral_case="WATCH/HOLD outcomes should be interpreted as monitoring states, not proof of future returns.",
            key_assumptions=[
                "The active data provider output is accepted as the available evidence set.",
                "No real broker, portfolio, or order execution context is connected.",
                f"Research objective: {request.research_objective}.",
            ],
            catalysts=news.catalysts,
            risks=[item.description for item in risk_review.risks],
            valuation_view=valuation_view,
            technical_view=technical_view,
            macro_view=macro_view,
            time_horizon=request.time_horizon,
            thesis_breakers=decision.invalidation_conditions,
            monitoring_conditions=[
                *decision.invalidation_conditions,
                *decision.risk_warnings,
            ],
            missing_information=missing_information,
            evidence_coverage="partial" if missing_information else "broad",
            confidence=confidence,
            recommendation=decision.decision,
            recommendation_limitations=[
                "This is not a guaranteed result or personalized financial advice.",
                "No live trading, short selling, leverage, or execution path is included.",
                "Resolve missing information before treating the thesis as high conviction.",
            ],
        )

    def _build_committee_decision(
        self,
        *,
        decision: DecisionResponse,
        specialist_outputs: list[SpecialistResearchOutput],
        risk_review: StructuredRiskReview,
        confidence: ConfidenceAssessment,
    ) -> CommitteeResearchDecision:
        disagreements = [
            f"{output.module_name} is {output.status} while committee decision is {decision.decision}."
            for output in specialist_outputs
            if output.status != ResearchDimensionStatus.AVAILABLE
        ]
        dominant_risks = [item.description for item in risk_review.risks if item.severity in {RiskSeverity.HIGH, RiskSeverity.EXTREME}]
        return CommitteeResearchDecision(
            decision=decision.decision,
            decision_rationale=decision.final_explanation,
            supporting_module_decisions=[
                f"{output.module_name}: {output.conclusion}" for output in specialist_outputs
            ],
            disagreements=disagreements,
            dominant_risks=dominant_risks,
            confidence=confidence,
            conditions_required_for_upgrade=[
                "Verified external data improves coverage.",
                "Risk veto clears, if present.",
                "Missing valuation, filings, news, and macro inputs are resolved.",
            ],
            conditions_requiring_downgrade=[
                "Data quality becomes degraded or unavailable.",
                "Price action violates invalidation conditions.",
                "New verified evidence contradicts the thesis.",
            ],
            monitoring_checklist=[
                *decision.invalidation_conditions,
                *decision.risk_warnings,
            ],
        )

    def _stage_statuses(
        self,
        plan: ResearchPlan,
        specialists: list[SpecialistResearchOutput],
        missing_information: list[str],
    ) -> list[ResearchStageStatus]:
        failed = [output.module_name for output in specialists if output.status == ResearchDimensionStatus.FAILED]
        partial = [dimension.name for dimension in plan.dimensions if dimension.status == ResearchDimensionStatus.PARTIALLY_AVAILABLE]
        stages = [
            ("request_validation", "completed", "Research request validated."),
            ("research_plan", "completed", "Research dimensions were planned with explicit availability states."),
            ("evidence_collection", "partial" if missing_information else "completed", "Available evidence was normalized; missing information is listed."),
            ("specialist_analysis", "partial" if partial else "completed", "Specialist modules generated structured outputs from available evidence."),
            ("risk_review", "completed", "Risk manager output was converted into structured risk categories."),
            ("committee_decision", "completed", "Committee decision preserved deterministic risk controls."),
            ("persistence", "pending", "Report is attached to the decision payload before repository save."),
        ]
        if failed:
            stages.append(("module_errors", "failed", f"Failed modules: {', '.join(failed)}."))
        return [ResearchStageStatus(stage=stage, status=status, message=message) for stage, status, message in stages]

    def _missing_information(self, plan: ResearchPlan, evidence: list[EvidenceItem]) -> list[str]:
        missing = [
            f"{dimension.name}: {'; '.join(dimension.limitations) or 'unavailable'}"
            for dimension in plan.dimensions
            if dimension.status in {ResearchDimensionStatus.UNAVAILABLE, ResearchDimensionStatus.FAILED}
        ]
        missing.extend(
            item.summary
            for item in evidence
            if item.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE
        )
        return list(dict.fromkeys(missing))

    def _evidence(
        self,
        evidence_id: str,
        category: str,
        title: str,
        summary: str,
        value,
        source_type: EvidenceSourceType,
        source_name: str,
        observed_at: str,
        evidence_kind: EvidenceKind,
        availability_status: EvidenceAvailabilityStatus,
        *,
        confidence: float,
        limitation: str | None,
        source_metadata: DataSourceMetadata | None = None,
        freshness: FreshnessStatus | None = None,
        period_start: str | None = None,
        period_end: str | None = None,
        formula: str | None = None,
    ) -> EvidenceItem:
        resolved_freshness = freshness or (
            FreshnessStatus.FRESH if availability_status == EvidenceAvailabilityStatus.AVAILABLE else FreshnessStatus.UNKNOWN
        )
        return EvidenceItem(
            evidence_id=evidence_id,
            category=category,
            title=title,
            summary=summary,
            value=value,
            source_type=source_type,
            source_name=source_name,
            source_reference=source_metadata.source_reference if source_metadata else None,
            provider_symbol=source_metadata.provider_symbol if source_metadata else None,
            observed_at=source_metadata.observed_at or observed_at if source_metadata else observed_at,
            fetched_at=source_metadata.fetched_at if source_metadata else None,
            period_start=period_start or (source_metadata.period_start if source_metadata else None),
            period_end=period_end or (source_metadata.period_end if source_metadata else None),
            currency=source_metadata.currency if source_metadata else None,
            delayed=source_metadata.delayed if source_metadata else False,
            delayed_by=source_metadata.delayed_by if source_metadata else None,
            transformation_type=source_metadata.transformation_type if source_metadata else None,
            is_derived=bool(source_metadata.is_derived) if source_metadata else evidence_kind == EvidenceKind.DERIVED_CALCULATION,
            formula=formula or (source_metadata.formula if source_metadata else None),
            warnings=source_metadata.warnings if source_metadata else [],
            freshness_status=resolved_freshness,
            confidence=max(0, min(1, confidence)),
            availability_status=availability_status,
            error_or_limitation=limitation,
            evidence_kind=evidence_kind,
        )

    def _unavailable_evidence(
        self,
        evidence_id: str,
        category: str,
        title: str,
        summary: str,
        observed_at: str,
    ) -> EvidenceItem:
        return self._evidence(
            evidence_id,
            category,
            title,
            summary,
            None,
            EvidenceSourceType.UNAVAILABLE_SOURCE,
            "not_connected",
            observed_at,
            EvidenceKind.UNAVAILABLE_INFORMATION,
            EvidenceAvailabilityStatus.UNAVAILABLE,
            confidence=0,
            limitation=summary,
        )

    def _provider_source_type(self, provider: str, quality: str) -> EvidenceSourceType:
        if str(quality).upper() == "MOCK" or provider == "mock":
            return EvidenceSourceType.MOCK_DATA
        if str(quality).upper() == "REAL":
            return EvidenceSourceType.EXISTING_MARKET_DATA_SERVICE
        if str(quality).upper() in {"DEGRADED", "UNAVAILABLE"}:
            return EvidenceSourceType.EXISTING_MARKET_DATA_SERVICE
        return EvidenceSourceType.EXISTING_APPLICATION_DATA

    def _source_type_from_metadata(self, source: DataSourceMetadata) -> EvidenceSourceType:
        if source.source_type.value == "mock_data":
            return EvidenceSourceType.MOCK_DATA
        if source.source_type.value == "unavailable_source":
            return EvidenceSourceType.UNAVAILABLE_SOURCE
        return EvidenceSourceType.EXISTING_MARKET_DATA_SERVICE

    def _financial_snapshot(self, collected_data: dict) -> FinancialDataSnapshot | None:
        raw = collected_data.get("financial_data")
        if raw is None:
            return None
        if isinstance(raw, FinancialDataSnapshot):
            return raw
        try:
            return FinancialDataSnapshot.model_validate(raw)
        except Exception:
            return None

    def _availability_from_financial(self, status: FinancialDataAvailability) -> EvidenceAvailabilityStatus:
        if status == FinancialDataAvailability.AVAILABLE:
            return EvidenceAvailabilityStatus.AVAILABLE
        if status in {FinancialDataAvailability.PARTIAL, FinancialDataAvailability.STALE_CACHE}:
            return EvidenceAvailabilityStatus.PARTIAL
        if status == FinancialDataAvailability.FAILED:
            return EvidenceAvailabilityStatus.FAILED
        return EvidenceAvailabilityStatus.UNAVAILABLE

    def _freshness_from_financial(self, status: FinancialDataFreshness | None) -> FreshnessStatus:
        if status is None:
            return FreshnessStatus.UNKNOWN
        mapping = {
            FinancialDataFreshness.CURRENT: FreshnessStatus.CURRENT,
            FinancialDataFreshness.DELAYED: FreshnessStatus.DELAYED,
            FinancialDataFreshness.STALE: FreshnessStatus.STALE,
            FinancialDataFreshness.MATERIALLY_STALE: FreshnessStatus.MATERIALLY_STALE,
            FinancialDataFreshness.PARTIAL: FreshnessStatus.PARTIAL,
            FinancialDataFreshness.UNKNOWN: FreshnessStatus.UNKNOWN,
            FinancialDataFreshness.UNAVAILABLE: FreshnessStatus.UNAVAILABLE,
        }
        return mapping.get(status, FreshnessStatus.UNKNOWN)

    def _dimension_status_from_financial(self, status: FinancialDataAvailability) -> ResearchDimensionStatus:
        if status == FinancialDataAvailability.AVAILABLE:
            return ResearchDimensionStatus.AVAILABLE
        if status in {FinancialDataAvailability.PARTIAL, FinancialDataAvailability.STALE_CACHE}:
            return ResearchDimensionStatus.PARTIALLY_AVAILABLE
        if status == FinancialDataAvailability.FAILED:
            return ResearchDimensionStatus.FAILED
        return ResearchDimensionStatus.UNAVAILABLE

    def _snapshot_warnings(self, snapshot: FinancialDataSnapshot | None, component: str) -> list[str]:
        if snapshot is None:
            return []
        target = getattr(snapshot, component, None)
        if target is None:
            return []
        return list(getattr(target, "warnings", []))

    def _normalized_financial_keys(self, snapshot: FinancialDataSnapshot | None) -> set[str]:
        if snapshot is None:
            return set()
        keys = {metric.name for metric in snapshot.financial_metrics.metrics}
        keys.update(metric.name for metric in snapshot.valuation_metrics.metrics)
        keys.update({"revenue_growth", "profit_margins", "trailing_pe", "forward_pe"})
        return keys

    def _max_drawdown_from_bars(self, bars) -> float | None:
        closes = [bar.close for bar in bars if bar.close is not None]
        if len(closes) < 2:
            return None
        peak = closes[0]
        max_drawdown = 0.0
        for close in closes:
            peak = max(peak, close)
            if peak:
                max_drawdown = min(max_drawdown, (close / peak) - 1)
        return round(max_drawdown, 6)

    def _ids_by_category(self, evidence: list[EvidenceItem], category: str) -> list[str]:
        return [item.evidence_id for item in evidence if item.category == category]

    def _find_output(self, outputs: list[SpecialistResearchOutput], module_name: str) -> SpecialistResearchOutput:
        for output in outputs:
            if output.module_name == module_name:
                return output
        return SpecialistResearchOutput(
            module_name=module_name,
            status=ResearchDimensionStatus.UNAVAILABLE,
            conclusion=f"{module_name} is unavailable.",
            limitations=[f"{module_name} did not produce output."],
            missing_inputs=[module_name],
            confidence=0,
        )

    def _case_evidence_refs(self, case_name: str, outputs: list[SpecialistResearchOutput]) -> list[str]:
        if case_name == "bull":
            modules = {"technical_analysis", "fundamental_analysis", "catalyst_analysis"}
        else:
            modules = {"risk_analysis", "valuation_analysis", "macro_analysis"}
        refs: list[str] = []
        for output in outputs:
            if output.module_name in modules:
                refs.extend(output.supporting_evidence_ids)
                refs.extend(output.opposing_evidence_ids)
        return list(dict.fromkeys(refs))

    def _severity_from_quality(self, quality: str) -> RiskSeverity:
        normalized = str(quality).upper()
        if normalized == "REAL":
            return RiskSeverity.MEDIUM
        if normalized == "MOCK":
            return RiskSeverity.HIGH
        if normalized == "DEGRADED":
            return RiskSeverity.HIGH
        if normalized == "UNAVAILABLE":
            return RiskSeverity.EXTREME
        return RiskSeverity.UNKNOWN

    def _stringify_value(self, value):
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
