import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getDecisions } from "../api/client.js";
import Card from "../components/ui/Card.jsx";
import {
  formatConfidence,
  formatInstrument,
  formatPrice,
  formatTimestampCompact,
  truncateText
} from "../utils/formatting.js";
import { enumLabel } from "../utils/labels.js";

export default function DecisionLogPage({ onSelectDecision }) {
  const { t } = useTranslation();
  const [decisions, setDecisions] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getDecisions()
      .then((data) => setDecisions(data.items))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">{t("decisionLog.eyebrow")}</p>
          <h2>{t("decisionLog.title")}</h2>
          <p>{t("decisionLog.subtitle")}</p>
        </div>
      </div>

      {error && <Card className="error-card">{error}</Card>}

      <Card>
        <div className="table-scroll">
          <table className="data-table decision-log-table">
            <thead>
              <tr>
                <th>{t("common.timestamp")}</th>
                <th>{t("common.instrument")}</th>
                <th>{t("common.market")}</th>
                <th>{t("common.decision")}</th>
                <th>{t("common.provider")}</th>
                <th>{t("common.data")}</th>
                <th>{t("common.confidence")}</th>
                <th>{t("watchlist.latestPrice")}</th>
                <th>{t("decisionLog.explanation")}</th>
                <th>{t("common.inspect")}</th>
              </tr>
            </thead>
            <tbody>
              {decisions.map((item) => (
                <tr key={item.decision_id}>
                  <td className="cell-nowrap">{formatTimestampCompact(item.timestamp)}</td>
                  <td className="instrument-cell">
                    {formatInstrument(item.company_name, item.display_symbol, item.ticker)}
                  </td>
                  <td className="cell-nowrap">{item.market}</td>
                  <td className="cell-nowrap">{enumLabel(t, item.decision)}</td>
                  <td className="cell-nowrap">{item.data_provider || "mock"}</td>
                  <td className="cell-nowrap">{enumLabel(t, item.data_quality || "MOCK")}</td>
                  <td className="cell-nowrap">{formatConfidence(item.confidence)}</td>
                  <td className="cell-nowrap">{formatPrice(item.latest_price)}</td>
                  <td className="explanation-cell" title={item.final_explanation}>
                    <span className="cell-clamp-2">{truncateText(item.final_explanation, 180)}</span>
                  </td>
                  <td className="cell-nowrap">
                    <button className="link-button" onClick={() => onSelectDecision(item.decision_id)}>
                      {t("common.viewDetail")}
                    </button>
                  </td>
                </tr>
              ))}
              {decisions.length === 0 && (
                <tr>
                  <td colSpan="10" className="empty-cell">{t("decisionLog.noDecisions")}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
