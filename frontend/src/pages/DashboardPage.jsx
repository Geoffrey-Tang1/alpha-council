import { useEffect, useState } from "react";

import { getDecisions, getMarketStatus, getWatchlistSummary } from "../api/client.js";
import MarketStatusGrid from "../components/market/MarketStatusGrid.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { formatConfidence, formatDateTime } from "../utils/formatting.js";

export default function DashboardPage({ onNavigate, onSelectDecision }) {
  const [markets, setMarkets] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [watchlistSummary, setWatchlistSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getMarketStatus(), getDecisions(), getWatchlistSummary()])
      .then(([marketData, decisionData, watchlistData]) => {
        setMarkets(marketData.markets);
        setDecisions(decisionData.items.slice(0, 5));
        setWatchlistSummary(watchlistData);
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
          <p className="muted">Risk remains conservative when data is mock, degraded, or unavailable.</p>
        </Card>
        <Card>
          <h3>Quick Links</h3>
          <div className="quick-links">
            <Button onClick={() => onNavigate("analysis")}>New analysis</Button>
            <Button onClick={() => onNavigate("watchlist")}>Manage watchlist</Button>
            <Button onClick={() => onNavigate("evaluations")}>Evaluate decisions</Button>
            <Button onClick={() => onNavigate("decisions")}>Review decisions</Button>
          </div>
        </Card>
      </div>

      <Card>
        <div className="card-row">
          <div>
            <h3>Watchlist Risk Review</h3>
            <p className="muted">Lightweight research summary only. No portfolio accounting or live exposure tracking.</p>
          </div>
          <Button onClick={() => onNavigate("watchlist")}>Manage</Button>
        </div>
        <div className="metric-grid">
          <div>
            <span>Total watchlist items</span>
            <strong>{watchlistSummary?.total_items ?? 0}</strong>
          </div>
          <div>
            <span>High risk items</span>
            <strong>{watchlistSummary?.high_risk_count ?? 0}</strong>
          </div>
          <div>
            <span>Non-real data count</span>
            <strong>{watchlistSummary?.non_real_data_count ?? 0}</strong>
          </div>
        </div>
        <div className="summary-grid">
          <div>
            <h4>Markets</h4>
            <ul className="stack-list">
              {Object.entries(watchlistSummary?.count_by_market || {}).map(([key, value]) => (
                <li key={key}>{key}: {value}</li>
              ))}
              {Object.keys(watchlistSummary?.count_by_market || {}).length === 0 && <li>No watchlist items yet.</li>}
            </ul>
          </div>
          <div>
            <h4>Signals</h4>
            <ul className="stack-list">
              {Object.entries(watchlistSummary?.count_by_latest_signal || {}).map(([key, value]) => (
                <li key={key}>{key}: {value}</li>
              ))}
              {Object.keys(watchlistSummary?.count_by_latest_signal || {}).length === 0 && <li>No saved signals yet.</li>}
            </ul>
          </div>
          <div>
            <h4>Risk Levels</h4>
            <ul className="stack-list">
              {Object.entries(watchlistSummary?.count_by_latest_risk_level || {}).map(([key, value]) => (
                <li key={key}>{key}: {value}</li>
              ))}
              {Object.keys(watchlistSummary?.count_by_latest_risk_level || {}).length === 0 && <li>No risk levels yet.</li>}
            </ul>
          </div>
        </div>
        {watchlistSummary?.concentration_warning && (
          <p className="data-disclaimer">{watchlistSummary.concentration_warning}</p>
        )}
        {watchlistSummary?.data_quality_note && <p className="muted">{watchlistSummary.data_quality_note}</p>}
      </Card>

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
              <th>Data</th>
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
                <td>{decision.data_quality || "MOCK"}</td>
                <td>{formatConfidence(decision.confidence)}</td>
                <td>
                  <Button onClick={() => onSelectDecision(decision.decision_id)}>Open</Button>
                </td>
              </tr>
            ))}
            {decisions.length === 0 && (
              <tr>
                <td colSpan="7" className="empty-cell">No saved decisions yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
