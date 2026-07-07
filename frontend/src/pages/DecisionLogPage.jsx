import { useEffect, useState } from "react";

import { getDecisions } from "../api/client.js";
import Card from "../components/ui/Card.jsx";
import { formatConfidence, formatDateTime, formatPrice } from "../utils/formatting.js";

export default function DecisionLogPage({ onSelectDecision }) {
  const [decisions, setDecisions] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getDecisions()
      .then((data) => setDecisions(data.items))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Audit trail</p>
          <h2>Decision Log</h2>
          <p>Saved research decisions from the local Phase 1 SQLite database.</p>
        </div>
      </div>

      {error && <Card className="error-card">{error}</Card>}

      <Card>
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Ticker</th>
              <th>Market</th>
              <th>Decision</th>
              <th>Confidence</th>
              <th>Latest Price</th>
              <th>Explanation</th>
              <th>Inspect</th>
            </tr>
          </thead>
          <tbody>
            {decisions.map((item) => (
              <tr key={item.decision_id}>
                <td>{formatDateTime(item.timestamp)}</td>
                <td>{item.ticker}</td>
                <td>{item.market}</td>
                <td>{item.decision}</td>
                <td>{formatConfidence(item.confidence)}</td>
                <td>{formatPrice(item.latest_price)}</td>
                <td>{item.final_explanation}</td>
                <td>
                  <button className="link-button" onClick={() => onSelectDecision(item.decision_id)}>
                    Open payload
                  </button>
                </td>
              </tr>
            ))}
            {decisions.length === 0 && (
              <tr>
                <td colSpan="8" className="empty-cell">No decisions saved yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
