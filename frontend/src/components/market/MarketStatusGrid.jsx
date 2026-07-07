import Card from "../ui/Card.jsx";
import MarketStatusBadge from "./MarketStatusBadge.jsx";

export default function MarketStatusGrid({ markets = [] }) {
  return (
    <div className="market-grid">
      {markets.map((market) => (
        <Card key={market.market}>
          <div className="card-row">
            <div>
              <p className="eyebrow">{market.market}</p>
              <h3>{market.display_name}</h3>
            </div>
            <MarketStatusBadge status={market.status} />
          </div>
          <p className="muted">{market.timezone}</p>
          <p className="muted">
            Regular session {market.session.regular_open}-{market.session.regular_close}
          </p>
        </Card>
      ))}
    </div>
  );
}
