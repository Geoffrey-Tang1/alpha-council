import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getEvaluation, getEvaluations, getEvaluationSummary, runEvaluation } from "../api/client.js";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { formatConfidence, formatInstrument, formatPercent, formatTimestampCompact } from "../utils/formatting.js";
import { enumLabel } from "../utils/labels.js";

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
  const { t } = useTranslation();
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
          <p className="eyebrow">{t("evaluation.eyebrow")}</p>
          <h2>{t("evaluation.title")}</h2>
          <p>{t("evaluation.subtitle")}</p>
        </div>
        <div className="header-actions">
          <Button onClick={evaluateAll} disabled={running}>
            {running ? t("evaluation.evaluating") : t("evaluation.evaluateAll")}
          </Button>
          <Button onClick={() => loadData(filters)} disabled={loading}>{t("common.refresh")}</Button>
        </div>
      </div>

      {error && <Card className="error-card">{error}</Card>}

      <Card>
        <p className="data-disclaimer">
          {t("evaluation.disclaimer")}
        </p>
        {summary?.warning && <p className="muted">{summary.warning}</p>}
      </Card>

      <div className="metric-grid">
        <MetricTile label={t("evaluation.totalEvaluated")} value={summary?.total_evaluated ?? 0} />
        <MetricTile label={t("evaluation.favorable")} value={summary?.favorable_count ?? 0} />
        <MetricTile label={t("evaluation.unfavorable")} value={summary?.unfavorable_count ?? 0} />
        <MetricTile label={t("evaluation.neutral")} value={summary?.neutral_count ?? 0} />
        <MetricTile label={t("evaluation.insufficientData")} value={summary?.insufficient_data_count ?? 0} />
        <MetricTile label={t("evaluation.avg20dReturn")} value={formatPercent(summary?.average_forward_return_20d)} />
        <MetricTile label={t("evaluation.avg60dReturn")} value={formatPercent(summary?.average_forward_return_60d)} />
      </div>

      <Card>
        <form className="evaluation-filters" onSubmit={applyFilters}>
          <label>
            {t("common.ticker")}
            <input name="ticker" value={filters.ticker} onChange={updateFilter} placeholder="NVDA" />
          </label>
          <label>
            {t("common.market")}
            <select name="market" value={filters.market} onChange={updateFilter}>
              <option value="">{t("common.all")}</option>
              <option value="US">US</option>
              <option value="JP">JP</option>
              <option value="TW">TW</option>
              <option value="KR">KR</option>
            </select>
          </label>
          <label>
            {t("common.decision")}
            <select name="decision" value={filters.decision} onChange={updateFilter}>
              <option value="">{t("common.all")}</option>
              <option value="BUY">{enumLabel(t, "BUY")}</option>
              <option value="SELL">{enumLabel(t, "SELL")}</option>
              <option value="HOLD">{enumLabel(t, "HOLD")}</option>
              <option value="WATCH">{enumLabel(t, "WATCH")}</option>
              <option value="AVOID">{enumLabel(t, "AVOID")}</option>
            </select>
          </label>
          <label>
            {t("evaluation.direction")}
            <select name="directional_result" value={filters.directional_result} onChange={updateFilter}>
              <option value="">{t("common.all")}</option>
              <option value="FAVORABLE">{enumLabel(t, "FAVORABLE")}</option>
              <option value="UNFAVORABLE">{enumLabel(t, "UNFAVORABLE")}</option>
              <option value="NEUTRAL_MONITORING">{enumLabel(t, "NEUTRAL_MONITORING")}</option>
              <option value="NEUTRAL_HOLD">{enumLabel(t, "NEUTRAL_HOLD")}</option>
              <option value="MISSED_UPSIDE">{enumLabel(t, "MISSED_UPSIDE")}</option>
              <option value="INSUFFICIENT_DATA">{enumLabel(t, "INSUFFICIENT_DATA")}</option>
            </select>
          </label>
          <label>
            {t("common.confidence")}
            <select name="confidence_bucket" value={filters.confidence_bucket} onChange={updateFilter}>
              <option value="">{t("common.all")}</option>
              <option value="0.0-0.4">0.0-0.4</option>
              <option value="0.4-0.6">0.4-0.6</option>
              <option value="0.6-0.8">0.6-0.8</option>
              <option value="0.8-1.0">0.8-1.0</option>
            </select>
          </label>
          <Button type="submit" disabled={loading}>{loading ? t("common.loading") : t("common.applyFilters")}</Button>
        </form>
      </Card>

      <Card>
        <h3>{t("evaluation.evaluations")}</h3>
        <div className="table-scroll">
          <table className="data-table evaluation-table">
            <thead>
              <tr>
                <th>{t("common.instrument")}</th>
                <th>{t("common.market")}</th>
                <th>{t("common.decision")}</th>
                <th>{t("common.confidence")}</th>
                <th>{t("evaluation.decisionTime")}</th>
                <th>1d</th>
                <th>5d</th>
                <th>20d</th>
                <th>60d</th>
                <th>{t("evaluation.dd20d")}</th>
                <th>{t("evaluation.dd60d")}</th>
                <th>{t("evaluation.result")}</th>
                <th>{t("common.data")}</th>
                <th>{t("evaluation.evaluated")}</th>
              </tr>
            </thead>
            <tbody>
              {evaluations.map((item) => (
                <tr
                  key={item.evaluation_id}
                  className="clickable-row"
                  onClick={() => openEvaluation(item.evaluation_id)}
                >
                  <td className="instrument-cell">{formatInstrument(item.company_name, item.display_symbol, item.ticker)}</td>
                  <td className="cell-nowrap">{item.market}</td>
                  <td className="cell-nowrap">{enumLabel(t, item.decision)}</td>
                  <td className="cell-nowrap">{formatConfidence(item.confidence)}</td>
                  <td className="cell-nowrap">{formatTimestampCompact(item.decision_timestamp)}</td>
                  <td className="cell-nowrap">{formatPercent(item.forward_return_1d)}</td>
                  <td className="cell-nowrap">{formatPercent(item.forward_return_5d)}</td>
                  <td className="cell-nowrap">{formatPercent(item.forward_return_20d)}</td>
                  <td className="cell-nowrap">{formatPercent(item.forward_return_60d)}</td>
                  <td className="cell-nowrap">{formatPercent(item.max_drawdown_20d)}</td>
                  <td className="cell-nowrap">{formatPercent(item.max_drawdown_60d)}</td>
                  <td className="cell-nowrap"><Badge tone={resultTone(item.directional_result)}>{enumLabel(t, item.directional_result)}</Badge></td>
                  <td className="cell-nowrap"><Badge tone={qualityTone(item.data_quality)}>{enumLabel(t, item.data_quality)}</Badge></td>
                  <td className="cell-nowrap">{formatTimestampCompact(item.evaluated_at)}</td>
                </tr>
              ))}
              {evaluations.length === 0 && (
                <tr>
                  <td colSpan="14" className="empty-cell">{t("evaluation.noEvaluations")}</td>
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
              <h3>{formatInstrument(selectedEvaluation.company_name, selectedEvaluation.display_symbol, selectedEvaluation.ticker)} {t("evaluation.detail")}</h3>
              <p className="muted">{selectedEvaluation.evaluation_summary}</p>
            </div>
            <Badge tone={resultTone(selectedEvaluation.directional_result)}>
              {enumLabel(t, selectedEvaluation.directional_result)}
            </Badge>
          </div>
          <dl className="detail-list">
            <div>
              <dt>{t("evaluation.originalDecision")}</dt>
              <dd>{selectedEvaluation.decision_id}</dd>
            </div>
            <div>
              <dt>{t("evaluation.forwardReturns")}</dt>
              <dd>
                1d {formatPercent(selectedEvaluation.forward_return_1d)} · 5d{" "}
                {formatPercent(selectedEvaluation.forward_return_5d)} · 20d{" "}
                {formatPercent(selectedEvaluation.forward_return_20d)} · 60d{" "}
                {formatPercent(selectedEvaluation.forward_return_60d)}
              </dd>
            </div>
            <div>
              <dt>{t("evaluation.drawdownRunup")}</dt>
              <dd>
                {t("evaluation.dd20d")} {formatPercent(selectedEvaluation.max_drawdown_20d)} ·{" "}
                {t("evaluation.dd60d")} {formatPercent(selectedEvaluation.max_drawdown_60d)} ·{" "}
                {t("evaluation.runup20d")} {formatPercent(selectedEvaluation.max_runup_20d)} ·{" "}
                {t("evaluation.runup60d")}{" "}
                {formatPercent(selectedEvaluation.max_runup_60d)}
              </dd>
            </div>
            <div>
              <dt>{t("common.data")}</dt>
              <dd>
                {selectedEvaluation.data_provider} · {enumLabel(t, selectedEvaluation.data_quality)}
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
