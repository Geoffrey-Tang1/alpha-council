import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getDecision } from "../api/client.js";
import AgentOpinionCard from "../components/analysis/AgentOpinionCard.jsx";
import DecisionCard from "../components/analysis/DecisionCard.jsx";
import RiskPanel from "../components/analysis/RiskPanel.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { formatConfidence, formatDateTime, formatInstrument } from "../utils/formatting.js";
import { enumLabel } from "../utils/labels.js";

export default function DecisionDetailPage({ decisionId, onBack }) {
  const { t } = useTranslation();
  const [decision, setDecision] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!decisionId) {
      return;
    }

    getDecision(decisionId)
      .then(setDecision)
      .catch((err) => setError(err.message));
  }, [decisionId]);

  if (!decisionId) {
    return (
      <div className="page">
        <Card className="error-card">{t("decisionDetail.noDecisionSelected")}</Card>
        <Button onClick={onBack}>{t("decisionDetail.backToLog")}</Button>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">{t("decisionDetail.eyebrow")}</p>
          <h2>
            {decision
              ? `${formatInstrument(decision.company_name, decision.display_symbol, decision.ticker)} ${enumLabel(t, decision.decision)}`
              : t("decisionDetail.loadingDecision")}
          </h2>
          <p>{decision ? formatDateTime(decision.timestamp) : t("decisionDetail.loadingPayload")}</p>
        </div>
        <Button onClick={onBack}>{t("common.back")}</Button>
      </div>

      {error && <Card className="error-card">{error}</Card>}

      {decision && (
        <>
          <DecisionCard decision={decision} />
          <div className="data-quality-card">
            <Card>
              <h3>{t("decisionDetail.dataQuality")}</h3>
              <p>{decision.data_disclaimer}</p>
              <p className="muted">
                {t("common.provider")}: {decision.data_provider} · {t("common.quality")}:{" "}
                {enumLabel(t, decision.data_quality)}
              </p>
              {decision.data_warnings?.length > 0 && (
                <ul className="stack-list warning-list">
                  {decision.data_warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
          <RiskPanel
            warnings={decision.risk_warnings}
            invalidationConditions={decision.invalidation_conditions}
          />
          <div className="two-column">
            <AgentOpinionCard
              title={t("analysis.bullCase")}
              items={decision.bull_case.bull_points}
              secondary={decision.bull_case.supporting_evidence}
            />
            <AgentOpinionCard
              title={t("analysis.bearCase")}
              items={decision.bear_case.bear_points}
              secondary={decision.bear_case.risk_factors}
            />
          </div>
          <Card>
            <h3>{t("decisionDetail.agentVotes")}</h3>
            <div className="table-scroll">
              <table className="data-table agent-votes-table">
                <thead>
                  <tr>
                    <th>{t("analysis.agent")}</th>
                    <th>{t("analysis.vote")}</th>
                    <th>{t("common.confidence")}</th>
                  </tr>
                </thead>
                <tbody>
                  {decision.agent_votes.map((vote) => (
                    <tr key={vote.agent}>
                      <td>{vote.agent}</td>
                      <td>{enumLabel(t, vote.vote)}</td>
                      <td>{formatConfidence(vote.confidence)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <Card>
            <h3>{t("common.fullPayload")}</h3>
            <pre className="payload-viewer">{JSON.stringify(decision, null, 2)}</pre>
          </Card>
        </>
      )}
    </div>
  );
}
