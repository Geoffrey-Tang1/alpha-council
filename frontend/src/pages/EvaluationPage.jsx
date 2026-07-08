import { useEffect, useState } from "react";

import { getEvaluation, getEvaluations, getEvaluationSummary, runEvaluation } from "../api/client.js";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { formatConfidence, formatDateTime, formatPercent } from "../utils/formatting.js";

const initialFilters = {
  ticker: "",
  market: "",
  decision: "",
  directional_result: "",
  confidence_bucket: ""
};

function resultTone(result) {
  if (result === "FAVORABLE") {
    return "success";
  }
  if (["UNFAVORABLE", "MISSED_UPSIDE", "INSUFFICIENT_DATA"].includes(result)) {
    return "danger";
  }
  return "neutral";
}

function qualityTone(quality) {
  if (quality === "REAL") {
    return "success";
  }
  if (["DEGRADED", "UNAVAILABLE"].includes(quality)) {
    return "danger";
  }
  return "warning";
}

function confidenceBucketMin(bucket) {
  if (bucket === "0.4-0.6") return 0.4;
  if (bucket === "0.6-0.8") return 0.6;
  if (bucket === "0.8-1.0") return 0.8;
  return "";
}

function MetricTile({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default function EvaluationPage() {
  const [summary, setSummary] = useState(null);
  const [evaluations, setEvaluations] = useState([]);
  const [filters, setFilters] = useState(initialFilters);
  const [selectedEvaluation, setSelectedEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData(nextFilters = filters) {
    setLoading(true);
    setError("");
    try {
      const params = {
        ticker: nextFilters.ticker,
        market: nextFilters.market,
        decision: nextFilters.decision,
        directional_result: nextFilters.directional_result,
        min_confidence: confidenceBucketMin(nextFilters.confidence_bucket),
        limit: 100,
        offset: 0
      };
      const [summaryData, evaluationData] = await Promise.all([getEvaluationSummary(), getEvaluations(params)]);
      setSummary(summaryData);
      setEvaluations(evaluationData.items || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function updateFilter(event) {
    const { name, value } = event.target;
    setFilters((current) => ({ ...current, [name]: value }));
  }

  async function applyFilters(event) {
    event.preventDefault();
    await loadData(filters);
  }

  async function evaluateAll() {
    setRunning(true);
    setError("");
    try {
      await runEvaluation({ limit: 100, include_already_evaluated: false });
      await loadData(filters);
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  }

  async function openEvaluation(evaluationId) {
    try {
      const detail = await getEvaluation(evaluationId);
      setSelectedEvaluation(detail);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Research analytics</p>
          <h2>Decision Evaluation</h2>
          <p>
            Review what happened after saved AlphaCouncil decisions using historical provider rows. This is
            observational research, not a claim of future profitability.
          </p>
        </div>
        <div className="header-actions">
          <Button onClick={evaluateAll} disabled={running}>
            {running ? "Evaluating..." : "Evaluate All Eligible"}
          </Button>
          <Button onClick={() => loadData(filters)} disabled={loading}>Refresh</Button>
        </div>
      </div>

      {error && <Card className="error-card">{error}</Card>}

      <Card>
        <p className="data-disclaimer">
          Decision evaluation is historical and observational only. It does not prove future profitability.
        </p>
        {summary?.warning && <p className="muted">{summary.warning}</p>}
      </Card>

      <div className="metric-grid">
        <MetricTile label="Total evaluated" value={summary?.total_evaluated ?? 0} />
        <MetricTile label="Favorable" value={summary?.favorable_count ?? 0} />
        <MetricTile label="Unfavorable" value={summary?.unfavorable_count ?? 0} />
        <MetricTile label="Neutral" value={summary?.neutral_count ?? 0} />
        <MetricTile label="Insufficient data" value={summary?.insufficient_data_count ?? 0} />
        <MetricTile label="Avg 20d return" value={formatPercent(summary?.average_forward_return_20d)} />
        <MetricTile label="Avg 60d return" value={formatPercent(summary?.average_forward_return_60d)} />
      </div>

      <Card>
        <form className="evaluation-filters" onSubmit={applyFilters}>
          <label>
            Ticker
            <input name="ticker" value={filters.ticker} onChange={updateFilter} placeholder="NVDA" />
          </label>
          <label>
            Market
            <select name="market" value={filters.market} onChange={updateFilter}>
              <option value="">All</option>
              <option value="US">US</option>
              <option value="JP">JP</option>
              <option value="TW">TW</option>
              <option value="KR">KR</option>
            </select>
          </label>
          <label>
            Decision
            <select name="decision" value={filters.decision} onChange={updateFilter}>
              <option value="">All</option>
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
              <option value="HOLD">HOLD</option>
              <option value="WATCH">WATCH</option>
              <option value="AVOID">AVOID</option>
            </select>
          </label>
          <label>
            Direction
            <select name="directional_result" value={filters.directional_result} onChange={updateFilter}>
              <option value="">All</option>
              <option value="FAVORABLE">FAVORABLE</option>
              <option value="UNFAVORABLE">UNFAVORABLE</option>
              <option value="NEUTRAL_MONITORING">NEUTRAL_MONITORING</option>
              <option value="NEUTRAL_HOLD">NEUTRAL_HOLD</option>
              <option value="MISSED_UPSIDE">MISSED_UPSIDE</option>
              <option value="INSUFFICIENT_DATA">INSUFFICIENT_DATA</option>
            </select>
          </label>
          <label>
            Confidence
            <select name="confidence_bucket" value={filters.confidence_bucket} onChange={updateFilter}>
              <option value="">All</option>
              <option value="0.0-0.4">0.0-0.4</option>
              <option value="0.4-0.6">0.4-0.6</option>
              <option value="0.6-0.8">0.6-0.8</option>
              <option value="0.8-1.0">0.8-1.0</option>
            </select>
          </label>
          <Button type="submit" disabled={loading}>{loading ? "Loading..." : "Apply Filters"}</Button>
        </form>
      </Card>

      <Card>
        <h3>Evaluations</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Market</th>
                <th>Decision</th>
                <th>Confidence</th>
                <th>Decision Time</th>
                <th>1d</th>
                <th>5d</th>
                <th>20d</th>
                <th>60d</th>
                <th>DD 20d</th>
                <th>DD 60d</th>
                <th>Result</th>
                <th>Data</th>
                <th>Evaluated</th>
              </tr>
            </thead>
            <tbody>
              {evaluations.map((item) => (
                <tr
                  key={item.evaluation_id}
                  className="clickable-row"
                  onClick={() => openEvaluation(item.evaluation_id)}
                >
                  <td>{item.ticker}</td>
                  <td>{item.market}</td>
                  <td>{item.decision}</td>
                  <td>{formatConfidence(item.confidence)}</td>
                  <td>{formatDateTime(item.decision_timestamp)}</td>
                  <td>{formatPercent(item.forward_return_1d)}</td>
                  <td>{formatPercent(item.forward_return_5d)}</td>
                  <td>{formatPercent(item.forward_return_20d)}</td>
                  <td>{formatPercent(item.forward_return_60d)}</td>
                  <td>{formatPercent(item.max_drawdown_20d)}</td>
                  <td>{formatPercent(item.max_drawdown_60d)}</td>
                  <td><Badge tone={resultTone(item.directional_result)}>{item.directional_result}</Badge></td>
                  <td><Badge tone={qualityTone(item.data_quality)}>{item.data_quality}</Badge></td>
                  <td>{formatDateTime(item.evaluated_at)}</td>
                </tr>
              ))}
              {evaluations.length === 0 && (
                <tr>
                  <td colSpan="14" className="empty-cell">No evaluations match the current filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {selectedEvaluation && (
        <Card>
          <div className="card-row">
            <div>
              <h3>{selectedEvaluation.ticker} Evaluation Detail</h3>
              <p className="muted">{selectedEvaluation.evaluation_summary}</p>
            </div>
            <Badge tone={resultTone(selectedEvaluation.directional_result)}>
              {selectedEvaluation.directional_result}
            </Badge>
          </div>
          <dl className="detail-list">
            <div>
              <dt>Original decision</dt>
              <dd>{selectedEvaluation.decision_id}</dd>
            </div>
            <div>
              <dt>Forward returns</dt>
              <dd>
                1d {formatPercent(selectedEvaluation.forward_return_1d)} · 5d{" "}
                {formatPercent(selectedEvaluation.forward_return_5d)} · 20d{" "}
                {formatPercent(selectedEvaluation.forward_return_20d)} · 60d{" "}
                {formatPercent(selectedEvaluation.forward_return_60d)}
              </dd>
            </div>
            <div>
              <dt>Drawdown / runup</dt>
              <dd>
                DD20 {formatPercent(selectedEvaluation.max_drawdown_20d)} · DD60{" "}
                {formatPercent(selectedEvaluation.max_drawdown_60d)} · Runup20{" "}
                {formatPercent(selectedEvaluation.max_runup_20d)} · Runup60{" "}
                {formatPercent(selectedEvaluation.max_runup_60d)}
              </dd>
            </div>
            <div>
              <dt>Data</dt>
              <dd>
                {selectedEvaluation.data_provider} · {selectedEvaluation.data_quality}
              </dd>
            </div>
          </dl>
          <p className="data-disclaimer">{selectedEvaluation.data_disclaimer}</p>
          {selectedEvaluation.data_warnings?.length > 0 && (
            <ul className="stack-list warning-list">
              {selectedEvaluation.data_warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          )}
          <pre className="payload-viewer">{JSON.stringify(selectedEvaluation, null, 2)}</pre>
        </Card>
      )}
    </div>
  );
}
