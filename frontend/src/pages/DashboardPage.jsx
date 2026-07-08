import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getDecisions, getMarketStatus, getWatchlistSummary } from "../api/client.js";
import MarketStatusGrid from "../components/market/MarketStatusGrid.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { formatConfidence, formatInstrument, formatTimestampCompact } from "../utils/formatting.js";
import { enumLabel } from "../utils/labels.js";

export default function DashboardPage({ onNavigate, onSelectDecision }) {
  const { t } = useTranslation();
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
          <p className="eyebrow">{t("dashboard.eyebrow")}</p>
          <h2>{t("app.name")}</h2>
          <p>{t("dashboard.subtitle")}</p>
        </div>
        <div className="header-actions">
          <Button onClick={() => onNavigate("analysis")}>{t("dashboard.runAnalysis")}</Button>
          <Button onClick={() => onNavigate("watchlist")}>{t("sidebar.nav.watchlist")}</Button>
          <Button onClick={() => onNavigate("backtest")}>{t("sidebar.nav.backtest")}</Button>
          <Button onClick={() => onNavigate("evaluations")}>{t("dashboard.evaluation")}</Button>
          <Button onClick={() => onNavigate("decisions")}>{t("sidebar.nav.decisions")}</Button>
        </div>
      </div>

      {error && <Card className="error-card">{error}</Card>}
      <MarketStatusGrid markets={markets} />

      <div className="dashboard-band">
        <Card>
          <h3>{t("dashboard.globalRiskSummary")}</h3>
          <div className="metric-grid compact">
            <div>
              <span>{t("dashboard.openMarkets")}</span>
              <strong>{openMarkets}/{markets.length || 4}</strong>
            </div>
            <div>
              <span>{t("dashboard.recentWatchAvoid")}</span>
              <strong>{watchOrAvoidCount}</strong>
            </div>
          </div>
          <p className="muted">{t("dashboard.riskConservative")}</p>
        </Card>
        <Card>
          <h3>{t("dashboard.quickLinks")}</h3>
          <div className="quick-links">
            <Button onClick={() => onNavigate("analysis")}>{t("dashboard.newAnalysis")}</Button>
            <Button onClick={() => onNavigate("watchlist")}>{t("dashboard.manageWatchlist")}</Button>
            <Button onClick={() => onNavigate("evaluations")}>{t("dashboard.evaluateDecisions")}</Button>
            <Button onClick={() => onNavigate("decisions")}>{t("dashboard.reviewDecisions")}</Button>
          </div>
        </Card>
      </div>

      <Card>
        <div className="card-row">
          <div>
            <h3>{t("dashboard.watchlistRiskReview")}</h3>
            <p className="muted">{t("dashboard.watchlistRiskReviewSubtitle")}</p>
          </div>
          <Button onClick={() => onNavigate("watchlist")}>{t("dashboard.manage")}</Button>
        </div>
        <div className="metric-grid">
          <div>
            <span>{t("dashboard.totalWatchlistItems")}</span>
            <strong>{watchlistSummary?.total_items ?? 0}</strong>
          </div>
          <div>
            <span>{t("dashboard.highRiskItems")}</span>
            <strong>{watchlistSummary?.high_risk_count ?? 0}</strong>
          </div>
          <div>
            <span>{t("dashboard.nonRealDataCount")}</span>
            <strong>{watchlistSummary?.non_real_data_count ?? 0}</strong>
          </div>
        </div>
        <div className="summary-grid">
          <div>
            <h4>{t("dashboard.markets")}</h4>
            <ul className="stack-list">
              {Object.entries(watchlistSummary?.count_by_market || {}).map(([key, value]) => (
                <li key={key}>{key}: {value}</li>
              ))}
              {Object.keys(watchlistSummary?.count_by_market || {}).length === 0 && <li>{t("dashboard.noWatchlistItems")}</li>}
            </ul>
          </div>
          <div>
            <h4>{t("dashboard.signals")}</h4>
            <ul className="stack-list">
              {Object.entries(watchlistSummary?.count_by_latest_signal || {}).map(([key, value]) => (
                <li key={key}>{enumLabel(t, key)}: {value}</li>
              ))}
              {Object.keys(watchlistSummary?.count_by_latest_signal || {}).length === 0 && <li>{t("dashboard.noSavedSignals")}</li>}
            </ul>
          </div>
          <div>
            <h4>{t("dashboard.riskLevels")}</h4>
            <ul className="stack-list">
              {Object.entries(watchlistSummary?.count_by_latest_risk_level || {}).map(([key, value]) => (
                <li key={key}>{enumLabel(t, key)}: {value}</li>
              ))}
              {Object.keys(watchlistSummary?.count_by_latest_risk_level || {}).length === 0 && <li>{t("dashboard.noRiskLevels")}</li>}
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
          <h3>{t("dashboard.latestDecisions")}</h3>
          <Button onClick={() => onNavigate("decisions")}>{t("dashboard.viewAll")}</Button>
        </div>
        <div className="table-scroll">
          <table className="data-table dashboard-decisions-table">
            <thead>
              <tr>
                <th>{t("dashboard.time")}</th>
                <th>{t("common.instrument")}</th>
                <th>{t("common.market")}</th>
                <th>{t("common.decision")}</th>
                <th>{t("common.data")}</th>
                <th>{t("common.confidence")}</th>
                <th>{t("common.inspect")}</th>
              </tr>
            </thead>
            <tbody>
              {decisions.map((decision) => (
                <tr key={decision.decision_id}>
                  <td className="cell-nowrap">{formatTimestampCompact(decision.timestamp)}</td>
                  <td className="instrument-cell">
                    {formatInstrument(decision.company_name, decision.display_symbol, decision.ticker)}
                  </td>
                  <td className="cell-nowrap">{decision.market}</td>
                  <td className="cell-nowrap">{enumLabel(t, decision.decision)}</td>
                  <td className="cell-nowrap">{enumLabel(t, decision.data_quality || "MOCK")}</td>
                  <td className="cell-nowrap">{formatConfidence(decision.confidence)}</td>
                  <td className="cell-nowrap">
                    <Button onClick={() => onSelectDecision(decision.decision_id)}>{t("common.open")}</Button>
                  </td>
                </tr>
              ))}
              {decisions.length === 0 && (
                <tr>
                  <td colSpan="7" className="empty-cell">{t("dashboard.noSavedDecisions")}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
