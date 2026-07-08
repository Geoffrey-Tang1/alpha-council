import { useTranslation } from "react-i18next";

import { formatConfidence, formatInstrument, formatPrice } from "../../utils/formatting.js";
import { enumLabel } from "../../utils/labels.js";
import Badge from "../ui/Badge.jsx";
import Card from "../ui/Card.jsx";

export default function DecisionCard({ decision }) {
  const { t } = useTranslation();

  if (!decision) {
    return null;
  }

  const tone = decision.decision === "BUY" ? "success" : decision.decision === "AVOID" ? "danger" : "warning";
  const dataTone =
    decision.data_quality === "REAL"
      ? "success"
      : decision.data_quality === "UNAVAILABLE"
        ? "danger"
        : "warning";

  return (
    <Card className="decision-card">
      <div className="card-row">
        <div>
          <p className="eyebrow">{decision.market} · {decision.data_provider || "mock"}</p>
          <h3 className="instrument-title">
            {formatInstrument(decision.company_name, decision.display_symbol, decision.ticker)}
          </h3>
          <h2>{enumLabel(t, decision.decision)}</h2>
          <p className="muted">
            {t("analysis.inputTicker")}: {decision.ticker} · {t("analysis.normalizedTicker")}:{" "}
            {decision.normalized_ticker || decision.ticker}
          </p>
        </div>
        <div className="decision-badges">
          <Badge tone={dataTone}>{enumLabel(t, decision.data_quality)}</Badge>
          <Badge tone={tone}>{formatConfidence(decision.confidence)}</Badge>
        </div>
      </div>
      <div className="metric-grid">
        <div>
          <span>{t("decisionCard.latestPrice")}</span>
          <strong>{formatPrice(decision.latest_price)}</strong>
        </div>
        <div>
          <span>{t("decisionCard.stopLoss")}</span>
          <strong>{formatPrice(decision.stop_loss)}</strong>
        </div>
        <div>
          <span>{t("decisionCard.takeProfit")}</span>
          <strong>{formatPrice(decision.take_profit)}</strong>
        </div>
        <div>
          <span>{t("decisionCard.maxSize")}</span>
          <strong>{decision.max_position_size_pct}%</strong>
        </div>
      </div>
      <p>{decision.entry_plan}</p>
      <p className="muted">{decision.final_explanation}</p>
    </Card>
  );
}
