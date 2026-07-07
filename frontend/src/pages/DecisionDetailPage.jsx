import { useEffect, useState } from "react";

import { getDecision } from "../api/client.js";
import AgentOpinionCard from "../components/analysis/AgentOpinionCard.jsx";
import DecisionCard from "../components/analysis/DecisionCard.jsx";
import RiskPanel from "../components/analysis/RiskPanel.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { formatConfidence, formatDateTime } from "../utils/formatting.js";

export default function DecisionDetailPage({ decisionId, onBack }) {
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
        <Card className="error-card">No decision selected.</Card>
        <Button onClick={onBack}>Back to Decision Log</Button>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Decision detail</p>
          <h2>{decision ? `${decision.ticker} ${decision.decision}` : "Loading decision"}</h2>
          <p>{decision ? formatDateTime(decision.timestamp) : "Loading saved payload."}</p>
        </div>
        <Button onClick={onBack}>Back</Button>
      </div>

      {error && <Card className="error-card">{error}</Card>}

      {decision && (
        <>
          <DecisionCard decision={decision} />
          <div className="data-quality-card">
            <Card>
              <h3>Data Quality</h3>
              <p>{decision.data_disclaimer}</p>
              <p className="muted">
                Provider: {decision.data_quality.provider} · Quality: {decision.data_quality.quality} · Mock:{" "}
                {decision.data_quality.is_mock ? "yes" : "no"}
              </p>
            </Card>
          </div>
          <RiskPanel
            warnings={decision.risk_warnings}
            invalidationConditions={decision.invalidation_conditions}
          />
          <div className="two-column">
            <AgentOpinionCard
              title="Bull Case"
              items={decision.bull_case.bull_points}
              secondary={decision.bull_case.supporting_evidence}
            />
            <AgentOpinionCard
              title="Bear Case"
              items={decision.bear_case.bear_points}
              secondary={decision.bear_case.risk_factors}
            />
          </div>
          <Card>
            <h3>Agent Votes</h3>
            <table>
              <thead>
                <tr>
                  <th>Agent</th>
                  <th>Vote</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {decision.agent_votes.map((vote) => (
                  <tr key={vote.agent}>
                    <td>{vote.agent}</td>
                    <td>{vote.vote}</td>
                    <td>{formatConfidence(vote.confidence)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
          <Card>
            <h3>Full Payload</h3>
            <pre className="payload-viewer">{JSON.stringify(decision, null, 2)}</pre>
          </Card>
        </>
      )}
    </div>
  );
}
