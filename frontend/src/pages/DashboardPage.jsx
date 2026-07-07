import { useEffect, useState } from "react";

import { getMarketStatus } from "../api/client.js";
import MarketStatusGrid from "../components/market/MarketStatusGrid.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";

export default function DashboardPage({ onNavigate }) {
  const [markets, setMarkets] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getMarketStatus()
      .then((data) => setMarkets(data.markets))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Global equity decision platform</p>
          <h2>AlphaCouncil</h2>
          <p>
            A multi-agent research desk for explainable equity decisions, risk review, and decision logging.
          </p>
        </div>
        <div className="header-actions">
          <Button onClick={() => onNavigate("analysis")}>Run Analysis</Button>
          <Button onClick={() => onNavigate("decisions")}>Decision Log</Button>
        </div>
      </div>

      {error && <Card className="error-card">{error}</Card>}
      <MarketStatusGrid markets={markets} />

      <div className="dashboard-band">
        <Card>
          <h3>Risk Boundary</h3>
          <p>No live trading, no broker integration, and no real API keys are used in Phase 1.</p>
        </Card>
        <Card>
          <h3>Decision Types</h3>
          <p>BUY, SELL, HOLD, WATCH, and AVOID are research decisions, not order instructions.</p>
        </Card>
      </div>
    </div>
  );
}
