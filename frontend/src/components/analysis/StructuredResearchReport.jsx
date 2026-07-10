import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { formatConfidence } from "../../utils/formatting.js";
import { enumLabel } from "../../utils/labels.js";
import Badge from "../ui/Badge.jsx";
import Card from "../ui/Card.jsx";

export default function StructuredResearchReport({ report }) {
  const { t } = useTranslation();
  const evidenceById = useMemo(() => {
    const entries = report?.evidence || [];
    return Object.fromEntries(entries.map((item) => [item.evidence_id, item]));
  }, [report]);

  if (!report) {
    return (
      <Card className="research-report legacy-report">
        <p className="eyebrow">{t("research.legacyReport")}</p>
        <p className="muted">{t("research.legacyReportHelp")}</p>
      </Card>
    );
  }

  const thesis = report.investment_thesis;
  const committee = report.committee_decision;
  const confidence = report.confidence_assessment;

  return (
    <div className="research-report">
      <Card className="research-report-header">
        <div>
          <p className="eyebrow">{t("research.eyebrow")}</p>
          <h3>{t("research.title")}</h3>
          <p>{thesis?.executive_summary}</p>
        </div>
        <div className="research-badge-stack">
          <Badge tone={report.execution_status === "completed" ? "success" : "warning"}>
            {t(`research.executionStatus.${report.execution_status}`, { defaultValue: report.execution_status })}
          </Badge>
          <Badge tone="neutral">{report.schema_version}</Badge>
        </div>
      </Card>

      <Section title={t("research.executiveSummary")}>
        <p>{thesis?.executive_summary}</p>
      </Section>

      <Section title={t("research.committeeDecision")}>
        <div className="research-callout">
          <div>
            <span>{t("common.decision")}</span>
            <strong>{enumLabel(t, committee?.decision)}</strong>
          </div>
          <div>
            <span>{t("common.confidence")}</span>
            <strong>{confidenceLabel(t, committee?.confidence)}</strong>
          </div>
        </div>
        <p>{committee?.decision_rationale}</p>
        <List title={t("research.dominantRisks")} items={committee?.dominant_risks} />
        <List title={t("research.conditionsForUpgrade")} items={committee?.conditions_required_for_upgrade} />
        <List title={t("research.conditionsForDowngrade")} items={committee?.conditions_requiring_downgrade} />
      </Section>

      <Section title={t("research.confidenceDataQuality")}>
        <div className="research-grid">
          <Metric label={t("common.confidence")} value={confidenceLabel(t, confidence)} />
          <Metric label={t("research.completeness")} value={report.data_quality_summary?.overall_completeness} />
          <Metric label={t("research.unavailableDimensions")} value={(report.data_quality_summary?.unavailable_dimensions || []).length} />
          <Metric label={t("research.inferenceSections")} value={(report.data_quality_summary?.inference_heavy_sections || []).length} />
        </div>
        <p className="muted">{confidence?.methodology}</p>
        <List title={t("research.confidencePenalties")} items={confidence?.confidence_penalties} />
        <List title={t("research.unresolvedUncertainty")} items={confidence?.unresolved_uncertainty} />
      </Section>

      <Section title={t("research.investmentThesis")}>
        <p>{thesis?.thesis_statement}</p>
        <List title={t("research.recommendationLimitations")} items={thesis?.recommendation_limitations} />
      </Section>

      <div className="two-column">
        <CaseSection title={t("research.bullCase")} caseData={thesis?.bull_case} evidenceById={evidenceById} />
        <CaseSection title={t("research.bearCase")} caseData={thesis?.bear_case} evidenceById={evidenceById} />
      </div>

      <Section title={t("research.keyAssumptions")}>
        <List items={thesis?.key_assumptions} />
      </Section>

      <Section title={t("research.catalysts")}>
        <List items={thesis?.catalysts} emptyText={t("research.noCatalysts")} />
      </Section>

      <div className="research-module-grid">
        <ModuleSection title={t("research.valuationView")} output={thesis?.valuation_view} evidenceById={evidenceById} />
        <ModuleSection title={t("research.technicalView")} output={thesis?.technical_view} evidenceById={evidenceById} />
        <ModuleSection title={t("research.macroView")} output={thesis?.macro_view} evidenceById={evidenceById} />
      </div>

      <Section title={t("research.riskReview")}>
        <div className="table-scroll">
          <table className="data-table research-risk-table">
            <thead>
              <tr>
                <th>{t("research.category")}</th>
                <th>{t("research.description")}</th>
                <th>{t("research.severity")}</th>
                <th>{t("research.likelihood")}</th>
                <th>{t("research.monitoring")}</th>
              </tr>
            </thead>
            <tbody>
              {(report.risk_review?.risks || []).map((risk) => (
                <tr key={risk.risk_id}>
                  <td className="cell-nowrap">{risk.category}</td>
                  <td>{risk.description}</td>
                  <td><Badge tone={riskTone(risk.severity)}>{risk.severity}</Badge></td>
                  <td>{risk.likelihood}</td>
                  <td>{risk.mitigation_or_monitoring}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <div className="two-column">
        <Section title={t("research.thesisBreakers")}>
          <List items={thesis?.thesis_breakers} />
        </Section>
        <Section title={t("research.monitoringConditions")}>
          <List items={thesis?.monitoring_conditions} />
        </Section>
      </div>

      <Section title={t("research.missingInformation")}>
        <List items={report.missing_information} emptyText={t("research.noMissingInformation")} />
      </Section>

      <Section title={t("research.sourcesEvidence")}>
        <p className="muted">{report.source_attribution_note}</p>
        <div className="evidence-list">
          {(report.evidence || []).map((item) => (
            <article className="evidence-item" key={item.evidence_id}>
              <div className="evidence-item-header">
                <strong>{item.title}</strong>
                <EvidenceBadges item={item} />
              </div>
              <p>{item.summary}</p>
              {item.error_or_limitation && <p className="muted">{item.error_or_limitation}</p>}
              <small>{item.evidence_id} · {sourceTypeLabel(t, item.source_type)} · {item.source_name}</small>
            </article>
          ))}
        </div>
      </Section>

      <Section title={t("research.methodLimitations")}>
        <List items={report.method_and_limitations} />
        <details className="research-details">
          <summary>{t("research.pipelineStages")}</summary>
          <ul className="stack-list">
            {(report.stage_statuses || []).map((stage) => (
              <li key={stage.stage}>
                <strong>{stage.stage}</strong>: {stage.status} — {stage.message}
              </li>
            ))}
          </ul>
        </details>
      </Section>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <Card className="research-section">
      <h3>{title}</h3>
      {children}
    </Card>
  );
}

function CaseSection({ title, caseData, evidenceById }) {
  const { t } = useTranslation();
  return (
    <Section title={title}>
      <p>{caseData?.core_argument}</p>
      <List title={t("research.supportingFactors")} items={caseData?.supporting_factors} />
      <List title={t("research.requiredAssumptions")} items={caseData?.required_assumptions} />
      <List title={t("research.invalidationConditions")} items={caseData?.invalidation_conditions} />
      <EvidenceReferences ids={caseData?.evidence_references} evidenceById={evidenceById} />
    </Section>
  );
}

function ModuleSection({ title, output, evidenceById }) {
  const { t } = useTranslation();
  return (
    <Section title={title}>
      <div className="research-section-heading">
        <Badge tone={statusTone(output?.status)}>{statusLabel(t, output?.status)}</Badge>
        <span>{t("common.confidence")}: {formatConfidence(output?.confidence)}</span>
      </div>
      <p>{output?.conclusion}</p>
      <List title={t("research.assumptions")} items={output?.assumptions} />
      <List title={t("research.limitations")} items={output?.limitations} />
      <List title={t("research.missingInputs")} items={output?.missing_inputs} />
      <EvidenceReferences ids={[...(output?.supporting_evidence_ids || []), ...(output?.opposing_evidence_ids || [])]} evidenceById={evidenceById} />
    </Section>
  );
}

function Metric({ label, value }) {
  return (
    <div className="research-metric">
      <span>{label}</span>
      <strong>{value ?? "N/A"}</strong>
    </div>
  );
}

function List({ title, items = [], emptyText }) {
  const normalizedItems = (items || []).filter(Boolean);
  if (!normalizedItems.length && !emptyText) {
    return null;
  }
  return (
    <div className="research-list-block">
      {title && <h4>{title}</h4>}
      {normalizedItems.length ? (
        <ul className="stack-list">
          {normalizedItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="muted">{emptyText}</p>
      )}
    </div>
  );
}

function EvidenceReferences({ ids = [], evidenceById }) {
  const { t } = useTranslation();
  const normalizedIds = [...new Set(ids || [])].filter(Boolean);
  if (!normalizedIds.length) {
    return null;
  }
  return (
    <div className="evidence-reference-list">
      <h4>{t("research.evidenceReferences")}</h4>
      <div className="evidence-chip-row">
        {normalizedIds.map((id) => {
          const item = evidenceById[id];
          return (
            <span className="evidence-chip" key={id} title={item?.summary || id}>
              {item?.title || id}
            </span>
          );
        })}
      </div>
    </div>
  );
}

function EvidenceBadges({ item }) {
  const { t } = useTranslation();
  return (
    <span className="evidence-badges">
      <Badge tone={availabilityTone(item.availability_status)}>{availabilityLabel(t, item.availability_status)}</Badge>
      <Badge tone="neutral">{sourceTypeLabel(t, item.source_type)}</Badge>
    </span>
  );
}

function statusTone(status) {
  if (status === "available") return "success";
  if (status === "partially_available") return "warning";
  if (status === "unavailable" || status === "failed") return "danger";
  return "neutral";
}

function availabilityTone(status) {
  if (status === "available") return "success";
  if (status === "partial") return "warning";
  if (status === "unavailable" || status === "failed") return "danger";
  return "neutral";
}

function riskTone(severity) {
  if (severity === "high" || severity === "extreme") return "danger";
  if (severity === "medium" || severity === "unknown") return "warning";
  return "success";
}

function confidenceLabel(t, confidence) {
  if (!confidence) {
    return "N/A";
  }
  return `${t(`research.confidenceLevels.${confidence.level}`, { defaultValue: confidence.level })} (${formatConfidence(confidence.score)})`;
}

function statusLabel(t, status) {
  return t(`research.statuses.${status}`, { defaultValue: status || "N/A" });
}

function availabilityLabel(t, status) {
  return t(`research.availability.${status}`, { defaultValue: status || "N/A" });
}

function sourceTypeLabel(t, sourceType) {
  return t(`research.sourceTypes.${sourceType}`, { defaultValue: sourceType || "N/A" });
}
