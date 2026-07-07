import { useEffect, useState } from "react";

import { addWatchlistItem, deleteWatchlistItem, getWatchlist } from "../api/client.js";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { formatPrice } from "../utils/formatting.js";

const initialForm = {
  ticker: "",
  market: "US",
  notes: ""
};

export default function WatchlistPage({ onNavigate }) {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadWatchlist();
  }, []);

  async function loadWatchlist() {
    try {
      const data = await getWatchlist();
      setItems(data.items);
    } catch (err) {
      setError(err.message);
    }
  }

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submitWatchlistItem(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await addWatchlistItem(form);
      setForm(initialForm);
      await loadWatchlist();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function removeItem(id) {
    setError("");
    try {
      await deleteWatchlistItem(id);
      await loadWatchlist();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Research queue</p>
          <h2>Watchlist</h2>
          <p>Track tickers for future AlphaCouncil review. Signals remain mock-data based in this MVP.</p>
        </div>
      </div>

      <Card>
        <form className="watchlist-form" onSubmit={submitWatchlistItem}>
          <label>
            Ticker
            <input name="ticker" value={form.ticker} onChange={updateField} placeholder="NVDA" required />
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
            Notes
            <input name="notes" value={form.notes} onChange={updateField} placeholder="Reason to monitor" />
          </label>
          <Button type="submit" disabled={loading}>{loading ? "Adding..." : "Add Ticker"}</Button>
        </form>
      </Card>

      {error && <Card className="error-card">{error}</Card>}

      <Card>
        <table>
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Market</th>
              <th>Latest Signal</th>
              <th>Risk</th>
              <th>Latest Price</th>
              <th>Notes</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.ticker}</td>
                <td>{item.market}</td>
                <td>{item.latest_signal || "WATCH"}</td>
                <td>{item.latest_risk_level || "UNKNOWN"}</td>
                <td>{formatPrice(item.latest_price)}</td>
                <td>{item.notes || ""}</td>
                <td>
                  <div className="table-actions">
                    <Button onClick={() => onNavigate("analysis")}>Analyze</Button>
                    <Button onClick={() => removeItem(item.id)}>Remove</Button>
                  </div>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan="7" className="empty-cell">No watchlist items yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
