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
          <DecisionCard decision={decision} />
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
