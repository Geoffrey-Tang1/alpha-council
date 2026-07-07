import { useState } from "react";

import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";

const initialForm = {
  ticker: "NVDA",
  market: "US",
  start_date: "2025-01-01",
  end_date: "2025-12-31",
  strategy_name: "moving_average_crossover",
  initial_capital: "100000"
};

export default function BacktestPage() {
  const [form, setForm] = useState(initialForm);
  const [submitted, setSubmitted] = useState(false);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  function submitBacktest(event) {
    event.preventDefault();
    setSubmitted(true);
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Simulation workspace</p>
          <h2>Backtest</h2>
          <p>Phase 2 includes the backtest form shell only. It does not generate fake performance results.</p>
        </div>
      </div>

      <Card>
        <form className="backtest-form" onSubmit={submitBacktest}>
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
            Start date
            <input name="start_date" type="date" value={form.start_date} onChange={updateField} required />
          </label>
          <label>
            End date
            <input name="end_date" type="date" value={form.end_date} onChange={updateField} required />
          </label>
          <label>
            Strategy
            <select name="strategy_name" value={form.strategy_name} onChange={updateField}>
              <option value="moving_average_crossover">Moving average crossover</option>
              <option value="rsi_oversold_rebound">RSI oversold rebound</option>
              <option value="breakout_n_day_high">Breakout N-day high</option>
            </select>
          </label>
          <label>
            Initial capital
            <input name="initial_capital" type="number" min="1" value={form.initial_capital} onChange={updateField} />
          </label>
          <Button type="submit">Prepare Backtest</Button>
        </form>
      </Card>

      {submitted && (
        <Card>
          <h3>Backtest Engine Pending</h3>
          <p>
            Inputs are captured for the future backtesting engine. No simulated performance table, equity chart,
            or trade history is shown until real simulation logic is implemented.
          </p>
        </Card>
      )}
    </div>
  );
}
