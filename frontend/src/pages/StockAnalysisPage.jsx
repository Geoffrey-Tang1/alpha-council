import { useState } from "react";

import { runAnalysis } from "../api/client.js";
import AgentOpinionCard from "../components/analysis/AgentOpinionCard.jsx";
import DecisionCard from "../components/analysis/DecisionCard.jsx";
import RiskPanel from "../components/analysis/RiskPanel.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { formatConfidence } from "../utils/formatting.js";

const initialForm = {
  ticker: "NVDA",
  market: "US",
  time_horizon: "swing",
  strategy_preference: "moving_average_crossover"
};

export default function StockAnalysisPage() {
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
          <p className="eyebrow">Committee workflow</p>
          <h2>Stock Analysis</h2>
          <p>Run deterministic Phase 1 agents against mock data and save the decision.</p>
        </div>
      </div>

      <Card>
        <form className="analysis-form" onSubmit={submitAnalysis}>
          <label>
            Ticker
            <input name="ticker" value={form.ticker} onChange={updateField} required />
          </label>
          <label>
            Market
            <select name="market" value={form.market} onChange={updateField}>
              <option value="US">US</option>
              <option value="JP">JP</option>
              <option value="TW">TW</option>
              <option value="KR">KR</option>
            </select>
          </label>
          <label>
            Time horizon
            <select name="time_horizon" value={form.time_horizon} onChange={updateField}>
              <option value="intraday">Intraday</option>
              <option value="swing">Swing</option>
              <option value="medium_term">Medium term</option>
              <option value="long_term">Long term</option>
            </select>
          </label>
          <label>
            Strategy preference
            <select name="strategy_preference" value={form.strategy_preference} onChange={updateField}>
              <option value="moving_average_crossover">Moving average crossover</option>
              <option value="rsi_oversold_rebound">RSI oversold rebound</option>
              <option value="breakout_n_day_high">Breakout N-day high</option>
            </select>
          </label>
          <Button type="submit" disabled={loading}>{loading ? "Running..." : "Run Analysis"}</Button>
        </form>
      </Card>

      {error && <Card className="error-card">{error}</Card>}

      {decision && (
        <div className="analysis-results">
          <Card>
            <h3>Data Quality</h3>
            <p>{decision.data_disclaimer}</p>
            <p className="muted">
              Provider: {decision.data_provider} · Quality: {decision.data_quality}
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
              title="Technical Analysis"
              signal={decision.agent_outputs.technical_analysis.technical_signal}
              confidence={decision.agent_outputs.technical_analysis.confidence}
              explanation={decision.agent_outputs.technical_analysis.explanation}
              details={decision.agent_outputs.technical_analysis.key_indicators}
              risks={decision.agent_outputs.technical_analysis.risks}
            />
            <SpecialistAgentCard
              title="Fundamental Analysis"
              signal={decision.agent_outputs.fundamental_analysis.fundamental_signal}
              confidence={decision.agent_outputs.fundamental_analysis.confidence}
              explanation={decision.agent_outputs.fundamental_analysis.explanation}
              details={decision.agent_outputs.fundamental_analysis.key_metrics}
              risks={decision.agent_outputs.fundamental_analysis.risks}
            />
            <SpecialistAgentCard
              title="News and Sentiment"
              signal={decision.agent_outputs.news_sentiment.sentiment_signal}
              confidence={decision.agent_outputs.news_sentiment.confidence}
              explanation={decision.agent_outputs.news_sentiment.explanation}
              details={{ catalysts: decision.agent_outputs.news_sentiment.catalysts.join(", ") }}
              risks={decision.agent_outputs.news_sentiment.risks}
            />
            <SpecialistAgentCard
              title="Macro and Cross-Market"
              signal={decision.agent_outputs.macro_cross_market.macro_signal}
              confidence={decision.agent_outputs.macro_cross_market.confidence}
              explanation={decision.agent_outputs.macro_cross_market.explanation}
              details={{ factors: decision.agent_outputs.macro_cross_market.macro_factors.join(", ") }}
              risks={decision.agent_outputs.macro_cross_market.risks}
            />
            <SpecialistAgentCard
              title="Risk Manager"
              signal={decision.agent_outputs.risk_manager.risk_level}
              confidence={Math.max(0, Math.min(1, 0.7 + decision.agent_outputs.risk_manager.confidence_adjustment))}
              explanation={decision.agent_outputs.risk_manager.veto ? decision.agent_outputs.risk_manager.veto_reason : "Risk controls passed without a BUY veto."}
              details={{
                max_position_size_pct: decision.agent_outputs.risk_manager.max_position_size_pct,
                stop_loss_required: decision.agent_outputs.risk_manager.stop_loss_required ? "yes" : "no",
                veto: decision.agent_outputs.risk_manager.veto ? "yes" : "no"
              }}
              risks={decision.agent_outputs.risk_manager.risk_warnings}
            />
            <SpecialistAgentCard
              title="Portfolio Manager"
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
        </div>
      )}
    </div>
  );
}

function SpecialistAgentCard({ title, signal, confidence, explanation, details = {}, risks = [] }) {
  return (
    <Card>
      <div className="card-row">
        <h3>{title}</h3>
        <strong>{signal}</strong>
      </div>
      <p>{explanation}</p>
      <p className="muted">Confidence: {formatConfidence(confidence)}</p>
      {Object.keys(details).length > 0 && (
        <dl className="detail-list">
          {Object.entries(details).map(([key, value]) => (
            <div key={key}>
              <dt>{key}</dt>
              <dd>{String(value ?? "N/A")}</dd>
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
