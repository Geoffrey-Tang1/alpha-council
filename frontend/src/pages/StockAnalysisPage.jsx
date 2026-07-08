import { useState } from "react";
import { useTranslation } from "react-i18next";

import { runAnalysis } from "../api/client.js";
import AgentOpinionCard from "../components/analysis/AgentOpinionCard.jsx";
import DecisionCard from "../components/analysis/DecisionCard.jsx";
import RiskPanel from "../components/analysis/RiskPanel.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { formatConfidence } from "../utils/formatting.js";
import { enumLabel, strategyLabel } from "../utils/labels.js";

const initialForm = {
  ticker: "NVDA",
  market: "US",
  time_horizon: "swing",
  strategy_preference: "moving_average_crossover"
};

export default function StockAnalysisPage() {
  const { t } = useTranslation();
  const [form, setForm] = useState(initialForm);
  const [decision, setDecision] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submitAnalysis(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await runAnalysis(form);
      setDecision(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">{t("analysis.eyebrow")}</p>
          <h2>{t("analysis.title")}</h2>
          <p>{t("analysis.subtitle")}</p>
        </div>
      </div>

      <Card>
        <form className="analysis-form" onSubmit={submitAnalysis}>
          <label>
            {t("common.ticker")}
            <input name="ticker" value={form.ticker} onChange={updateField} required />
          </label>
          <label>
            {t("common.market")}
            <select name="market" value={form.market} onChange={updateField}>
              <option value="US">US</option>
              <option value="JP">JP</option>
              <option value="TW">TW</option>
              <option value="KR">KR</option>
            </select>
          </label>
          <label>
            {t("analysis.timeHorizon")}
            <select name="time_horizon" value={form.time_horizon} onChange={updateField}>
              <option value="intraday">{t("analysis.horizons.intraday")}</option>
              <option value="swing">{t("analysis.horizons.swing")}</option>
              <option value="medium_term">{t("analysis.horizons.medium_term")}</option>
              <option value="long_term">{t("analysis.horizons.long_term")}</option>
            </select>
          </label>
          <label>
            {t("analysis.strategyPreference")}
            <select name="strategy_preference" value={form.strategy_preference} onChange={updateField}>
              <option value="moving_average_crossover">{strategyLabel(t, "moving_average_crossover")}</option>
              <option value="rsi_oversold_rebound">{strategyLabel(t, "rsi_oversold_rebound")}</option>
              <option value="breakout_n_day_high">{strategyLabel(t, "breakout_n_day_high")}</option>
            </select>
          </label>
          <Button type="submit" disabled={loading}>{loading ? t("analysis.running") : t("analysis.run")}</Button>
        </form>
      </Card>

      {error && <Card className="error-card">{error}</Card>}

      {decision && (
        <div className="analysis-results">
          <Card>
            <h3>{t("analysis.dataQuality")}</h3>
            <p>{decision.data_disclaimer}</p>
            <p className="muted">
              {t("analysis.inputTicker")}: {decision.ticker} · {t("analysis.normalizedTicker")}:{" "}
              {decision.normalized_ticker || decision.ticker} · {t("common.market")}: {decision.market}
            </p>
            <p className="muted">
              {t("common.dataProvider")}: {decision.data_provider} · {t("common.dataQuality")}:{" "}
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
          <DecisionCard decision={decision} />
          <div className="agent-grid">
            <SpecialistAgentCard
              title={t("analysis.technicalAnalysis")}
              signal={decision.agent_outputs.technical_analysis.technical_signal}
              confidence={decision.agent_outputs.technical_analysis.confidence}
              explanation={decision.agent_outputs.technical_analysis.explanation}
              details={decision.agent_outputs.technical_analysis.key_indicators}
              risks={decision.agent_outputs.technical_analysis.risks}
            />
            <SpecialistAgentCard
              title={t("analysis.fundamentalAnalysis")}
              signal={decision.agent_outputs.fundamental_analysis.fundamental_signal}
              confidence={decision.agent_outputs.fundamental_analysis.confidence}
              explanation={decision.agent_outputs.fundamental_analysis.explanation}
              details={decision.agent_outputs.fundamental_analysis.key_metrics}
              risks={decision.agent_outputs.fundamental_analysis.risks}
            />
            <SpecialistAgentCard
              title={t("analysis.newsSentiment")}
              signal={decision.agent_outputs.news_sentiment.sentiment_signal}
              confidence={decision.agent_outputs.news_sentiment.confidence}
              explanation={decision.agent_outputs.news_sentiment.explanation}
              details={{ catalysts: decision.agent_outputs.news_sentiment.catalysts.join(", ") }}
              risks={decision.agent_outputs.news_sentiment.risks}
            />
            <SpecialistAgentCard
              title={t("analysis.macroCrossMarket")}
              signal={decision.agent_outputs.macro_cross_market.macro_signal}
              confidence={decision.agent_outputs.macro_cross_market.confidence}
              explanation={decision.agent_outputs.macro_cross_market.explanation}
              details={{ factors: decision.agent_outputs.macro_cross_market.macro_factors.join(", ") }}
              risks={decision.agent_outputs.macro_cross_market.risks}
            />
            <SpecialistAgentCard
              title={t("analysis.riskManager")}
              signal={decision.agent_outputs.risk_manager.risk_level}
              confidence={Math.max(0, Math.min(1, 0.7 + decision.agent_outputs.risk_manager.confidence_adjustment))}
              explanation={decision.agent_outputs.risk_manager.veto ? decision.agent_outputs.risk_manager.veto_reason : t("analysis.riskControlsPassed")}
              details={{
                max_position_size_pct: decision.agent_outputs.risk_manager.max_position_size_pct,
                stop_loss_required: decision.agent_outputs.risk_manager.stop_loss_required ? "yes" : "no",
                veto: decision.agent_outputs.risk_manager.veto ? "yes" : "no"
              }}
              risks={decision.agent_outputs.risk_manager.risk_warnings}
            />
            <SpecialistAgentCard
              title={t("analysis.portfolioManager")}
              signal={decision.agent_outputs.portfolio_manager.portfolio_fit}
              confidence={0.6}
              explanation={decision.agent_outputs.portfolio_manager.explanation}
              details={{
                recommended_position_size_pct: decision.agent_outputs.portfolio_manager.recommended_position_size_pct,
                concentration_warning: decision.agent_outputs.portfolio_manager.concentration_warning || "none"
              }}
              risks={decision.agent_outputs.portfolio_manager.concentration_warning ? [decision.agent_outputs.portfolio_manager.concentration_warning] : []}
            />
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
            <h3>{t("analysis.agentVotes")}</h3>
            <table>
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
          </Card>
        </div>
      )}
    </div>
  );
}

function SpecialistAgentCard({ title, signal, confidence, explanation, details = {}, risks = [] }) {
  const { t } = useTranslation();

  return (
    <Card className="agent-card">
      <div className="agent-card-header">
        <h3 className="agent-card-title">{title}</h3>
        <strong className="agent-card-badge">{enumLabel(t, signal)}</strong>
      </div>
      <p>{explanation}</p>
      <p className="muted">{t("common.confidence")}: {formatConfidence(confidence)}</p>
      {Object.keys(details).length > 0 && (
        <dl className="metric-list">
          {Object.entries(details).map(([key, value]) => (
            <div key={key} className={`metric-row ${isLongMetricValue(value) ? "metric-row-long" : ""}`}>
              <dt className="metric-key">{formatMetricLabel(t, key)}</dt>
              <dd className="metric-value">{formatMetricValue(value)}</dd>
            </div>
          ))}
        </dl>
      )}
      {risks.length > 0 && (
        <ul className="stack-list">
          {risks.map((risk) => (
            <li key={risk}>{risk}</li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function formatMetricLabel(t, key) {
  const translated = t(`metrics.${key}`, { defaultValue: "" });
  if (translated) {
    return translated;
  }

  const acronyms = {
    cagr: "CAGR",
    macd: "MACD",
    pe: "P/E",
    pct: "Pct",
    rsi: "RSI",
    yoy: "YoY"
  };

  return key
    .split("_")
    .map((part) => acronyms[part.toLowerCase()] || `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(" ");
}

function formatMetricValue(value) {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
  }
  return String(value);
}

function isLongMetricValue(value) {
  const text = formatMetricValue(value);
  return text.length > 30 || text.includes(",");
}
