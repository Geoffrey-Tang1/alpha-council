import { formatConfidence, formatPrice } from "../../utils/formatting.js";
import Badge from "../ui/Badge.jsx";
import Card from "../ui/Card.jsx";

export default function DecisionCard({ decision }) {
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
          <p className="eyebrow">{decision.ticker} · {decision.market}</p>
          <h2>{decision.decision}</h2>
        </div>
        <div className="decision-badges">
          <Badge tone={dataTone}>{decision.data_quality}</Badge>
          <Badge tone={tone}>{formatConfidence(decision.confidence)}</Badge>
        </div>
      </div>
      <div className="metric-grid">
        <div>
          <span>Latest price</span>
          <strong>{formatPrice(decision.latest_price)}</strong>
        </div>
        <div>
          <span>Stop loss</span>
          <strong>{formatPrice(decision.stop_loss)}</strong>
        </div>
        <div>
          <span>Take profit</span>
          <strong>{formatPrice(decision.take_profit)}</strong>
        </div>
        <div>
          <span>Max size</span>
          <strong>{decision.max_position_size_pct}%</strong>
        </div>
      </div>
      <p>{decision.entry_plan}</p>
      <p className="muted">{decision.final_explanation}</p>
    </Card>
  );
}
