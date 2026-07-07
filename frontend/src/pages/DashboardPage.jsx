import { useEffect, useState } from "react";

import { getDecisions, getMarketStatus } from "../api/client.js";
import MarketStatusGrid from "../components/market/MarketStatusGrid.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { formatConfidence, formatDateTime } from "../utils/formatting.js";

export default function DashboardPage({ onNavigate, onSelectDecision }) {
  const [markets, setMarkets] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getMarketStatus(), getDecisions()])
      .then(([marketData, decisionData]) => {
        setMarkets(marketData.markets);
        setDecisions(decisionData.items.slice(0, 5));
      })
      .catch((err) => setError(err.message));
  }, []);

  const openMarkets = markets.filter((market) => market.status === "OPEN").length;
  const watchOrAvoidCount = decisions.filter((item) => ["WATCH", "AVOID"].includes(item.decision)).length;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Global equity decision platform</p>
          <h2>AlphaCouncil</h2>
          <p>
            A multi-agent research desk for explainable equity decisions, risk review, and decision logging.
          </p>
        </div>
        <div className="header-actions">
          <Button onClick={() => onNavigate("analysis")}>Run Analysis</Button>
          <Button onClick={() => onNavigate("watchlist")}>Watchlist</Button>
          <Button onClick={() => onNavigate("backtest")}>Backtest</Button>
          <Button onClick={() => onNavigate("decisions")}>Decision Log</Button>
        </div>
      </div>

      {error && <Card className="error-card">{error}</Card>}
      <MarketStatusGrid markets={markets} />

      <div className="dashboard-band">
        <Card>
          <h3>Global Risk Summary</h3>
          <div className="metric-grid compact">
            <div>
              <span>Open markets</span>
              <strong>{openMarkets}/{markets.length || 4}</strong>
            </div>
            <div>
              <span>Recent WATCH/AVOID</span>
              <strong>{watchOrAvoidCount}</strong>
            </div>
          </div>
          <p className="muted">Risk remains conservative while all market data is mocked.</p>
        </Card>
        <Card>
          <h3>Quick Links</h3>
          <div className="quick-links">
            <Button onClick={() => onNavigate("analysis")}>New analysis</Button>
            <Button onClick={() => onNavigate("watchlist")}>Manage watchlist</Button>
            <Button onClick={() => onNavigate("decisions")}>Review decisions</Button>
          </div>
        </Card>
      </div>

      <Card>
        <div className="card-row">
          <h3>Latest Decisions</h3>
          <Button onClick={() => onNavigate("decisions")}>View All</Button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Ticker</th>
              <th>Market</th>
              <th>Decision</th>
              <th>Confidence</th>
              <th>Inspect</th>
            </tr>
          </thead>
          <tbody>
            {decisions.map((decision) => (
              <tr key={decision.decision_id}>
                <td>{formatDateTime(decision.timestamp)}</td>
                <td>{decision.ticker}</td>
                <td>{decision.market}</td>
                <td>{decision.decision}</td>
                <td>{formatConfidence(decision.confidence)}</td>
                <td>
                  <Button onClick={() => onSelectDecision(decision.decision_id)}>Open</Button>
                </td>
              </tr>
            ))}
            {decisions.length === 0 && (
              <tr>
                <td colSpan="6" className="empty-cell">No saved decisions yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
