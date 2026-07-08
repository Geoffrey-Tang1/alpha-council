import { useEffect, useMemo, useState } from "react";

import { getBacktests, runBacktest } from "../api/client.js";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { formatCurrency, formatDateTime, formatPercent, formatPrice } from "../utils/formatting.js";

const initialForm = {
  ticker: "NVDA",
  market: "US",
  start_date: "2023-01-01",
  end_date: "2024-12-31",
  strategy_name: "moving_average_crossover",
  initial_capital: "100000",
  transaction_cost_bps: "5",
  slippage_bps: "10"
};

function qualityTone(quality) {
  if (quality === "REAL") {
    return "success";
  }
  if (quality === "DEGRADED" || quality === "UNAVAILABLE") {
    return "danger";
  }
  return "warning";
}

function EquityCurveChart({ points }) {
  const chartPoints = useMemo(() => {
    if (!points || points.length === 0) {
      return "";
    }

    const width = 640;
    const height = 220;
    const padding = 24;
    const equities = points.map((point) => point.equity);
    const min = Math.min(...equities);
    const max = Math.max(...equities);
    const range = max - min || 1;

    return points
      .map((point, index) => {
        const x = padding + (index / Math.max(points.length - 1, 1)) * (width - padding * 2);
        const y = height - padding - ((point.equity - min) / range) * (height - padding * 2);
        return `${x.toFixed(2)},${y.toFixed(2)}`;
      })
      .join(" ");
  }, [points]);

  if (!points || points.length === 0) {
    return <p className="muted">No equity curve was produced for this backtest.</p>;
  }

  const first = points[0];
  const last = points[points.length - 1];

  return (
    <div className="equity-chart" role="img" aria-label="Equity curve">
      <svg viewBox="0 0 640 220" preserveAspectRatio="none">
        <line x1="24" y1="196" x2="616" y2="196" />
        <line x1="24" y1="24" x2="24" y2="196" />
        <polyline points={chartPoints} />
      </svg>
      <div className="chart-labels">
        <span>
          {first.date}: {formatCurrency(first.equity)}
        </span>
        <span>
          {last.date}: {formatCurrency(last.equity)}
        </span>
      </div>
    </div>
  );
}

function MetricTile({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default function BacktestPage() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    setHistoryLoading(true);
    try {
      const response = await getBacktests();
      setHistory(response.items || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setHistoryLoading(false);
    }
  }

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submitBacktest(event) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const payload = {
        ...form,
        initial_capital: Number(form.initial_capital),
        transaction_cost_bps: Number(form.transaction_cost_bps),
        slippage_bps: Number(form.slippage_bps)
      };
      const response = await runBacktest(payload);
      setResult(response);
      await loadHistory();
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
          <p className="eyebrow">Historical simulation</p>
          <h2>Backtest</h2>
          <p>
            Run single-ticker, long-only strategy simulations using the selected AlphaCouncil data provider.
            Results are research artifacts, not performance promises.
          </p>
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
            <input
              name="initial_capital"
              type="number"
              min="1"
              value={form.initial_capital}
              onChange={updateField}
              required
            />
          </label>
          <label>
            Transaction cost bps
            <input
              name="transaction_cost_bps"
              type="number"
              min="0"
              value={form.transaction_cost_bps}
              onChange={updateField}
            />
          </label>
          <label>
            Slippage bps
            <input name="slippage_bps" type="number" min="0" value={form.slippage_bps} onChange={updateField} />
          </label>
          <Button type="submit" disabled={loading}>
            {loading ? "Running..." : "Run Backtest"}
          </Button>
        </form>
      </Card>

      {error && <Card className="error-card">{error}</Card>}

      {result && (
        <div className="analysis-results">
          <Card>
            <div className="card-row">
              <div>
                <p className="eyebrow">Simulation result</p>
                <h3>
                  {result.ticker} · {result.strategy_name}
                </h3>
                <p className="muted">{result.warning}</p>
              </div>
              <div className="decision-badges">
                <Badge tone="neutral">{result.data_provider}</Badge>
                <Badge tone={qualityTone(result.data_quality)}>{result.data_quality}</Badge>
              </div>
            </div>

            <p className="data-disclaimer">{result.data_disclaimer}</p>
            {result.data_warnings?.length > 0 && (
              <ul className="stack-list warning-list">
                {result.data_warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            )}

            <div className="metric-grid">
              <MetricTile label="Total return" value={formatPercent(result.total_return)} />
              <MetricTile label="CAGR" value={formatPercent(result.cagr)} />
              <MetricTile label="Max drawdown" value={formatPercent(result.max_drawdown)} />
              <MetricTile label="Win rate" value={formatPercent(result.win_rate)} />
              <MetricTile label="Trades" value={result.number_of_trades} />
              <MetricTile label="Avg trade return" value={formatPercent(result.average_trade_return)} />
            </div>
          </Card>

          <Card>
            <h3>Equity Curve</h3>
            <EquityCurveChart points={result.equity_curve} />
          </Card>

          <Card>
            <h3>Trade Log</h3>
            {result.trade_log.length === 0 ? (
              <p className="muted">No closed trades were generated for this simulation.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Entry</th>
                      <th>Entry Price</th>
                      <th>Exit</th>
                      <th>Exit Price</th>
                      <th>Return</th>
                      <th>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trade_log.map((trade, index) => (
                      <tr key={`${trade.entry_date}-${trade.exit_date}-${index}`}>
                        <td>{trade.entry_date}</td>
                        <td>{formatPrice(trade.entry_price)}</td>
                        <td>{trade.exit_date}</td>
                        <td>{formatPrice(trade.exit_price)}</td>
                        <td>{formatPercent(trade.return_pct)}</td>
                        <td>{trade.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          <Card>
            <details>
              <summary>Raw JSON</summary>
              <pre className="payload-viewer">{JSON.stringify(result, null, 2)}</pre>
            </details>
          </Card>
        </div>
      )}

      <Card>
        <div className="card-row">
          <div>
            <h3>Backtest History</h3>
            <p className="muted">Recent saved simulation runs.</p>
          </div>
          <Button type="button" onClick={loadHistory} disabled={historyLoading}>
            Refresh
          </Button>
        </div>
        {history.length === 0 ? (
          <p className="empty-cell">{historyLoading ? "Loading..." : "No backtests saved yet."}</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Created</th>
                  <th>Ticker</th>
                  <th>Market</th>
                  <th>Strategy</th>
                  <th>Data</th>
                  <th>Total Return</th>
                  <th>Trades</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.backtest_id}>
                    <td>{formatDateTime(item.created_at)}</td>
                    <td>{item.ticker}</td>
                    <td>{item.market}</td>
                    <td>{item.strategy_name}</td>
                    <td>
                      {item.data_provider} · {item.data_quality}
                    </td>
                    <td>{formatPercent(item.total_return)}</td>
                    <td>{item.number_of_trades}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
