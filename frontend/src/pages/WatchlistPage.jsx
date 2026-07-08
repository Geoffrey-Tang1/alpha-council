import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { addWatchlistItem, deleteWatchlistItem, getWatchlist } from "../api/client.js";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { formatInstrument, formatPrice } from "../utils/formatting.js";
import { enumLabel } from "../utils/labels.js";

const initialForm = {
  ticker: "",
  market: "US",
  notes: ""
};

export default function WatchlistPage({ onNavigate }) {
  const { t } = useTranslation();
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
          <p className="eyebrow">{t("watchlist.eyebrow")}</p>
          <h2>{t("watchlist.title")}</h2>
          <p>{t("watchlist.subtitle")}</p>
        </div>
      </div>

      <Card>
        <form className="watchlist-form" onSubmit={submitWatchlistItem}>
          <label>
            {t("common.ticker")}
            <input name="ticker" value={form.ticker} onChange={updateField} placeholder="NVDA" required />
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
            {t("common.notes")}
            <input name="notes" value={form.notes} onChange={updateField} placeholder={t("watchlist.notesPlaceholder")} />
          </label>
          <Button type="submit" disabled={loading}>{loading ? t("watchlist.adding") : t("watchlist.addTicker")}</Button>
        </form>
      </Card>

      {error && <Card className="error-card">{error}</Card>}

      <Card>
        <div className="table-scroll">
          <table className="data-table watchlist-table">
            <thead>
              <tr>
                <th>{t("common.instrument")}</th>
                <th>{t("common.market")}</th>
                <th>{t("watchlist.latestSignal")}</th>
                <th>{t("common.risk")}</th>
                <th>{t("watchlist.latestPrice")}</th>
                <th>{t("common.notes")}</th>
                <th>{t("common.actions")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="instrument-cell">{formatInstrument(item.company_name, item.display_symbol, item.ticker)}</td>
                  <td className="cell-nowrap">{item.market}</td>
                  <td className="cell-nowrap">{enumLabel(t, item.latest_signal || "WATCH")}</td>
                  <td className="cell-nowrap">{enumLabel(t, item.latest_risk_level || "UNKNOWN")}</td>
                  <td className="cell-nowrap">{formatPrice(item.latest_price)}</td>
                  <td>{item.notes || ""}</td>
                  <td className="cell-nowrap">
                    <div className="table-actions">
                      <Button onClick={() => onNavigate("analysis")}>{t("common.analyze")}</Button>
                      <Button onClick={() => removeItem(item.id)}>{t("common.remove")}</Button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan="7" className="empty-cell">{t("watchlist.noItems")}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
