import Card from "../ui/Card.jsx";

export default function RiskPanel({ warnings = [], invalidationConditions = [] }) {
  return (
    <Card>
      <h3>Risk Review</h3>
      <ul className="stack-list">
        {warnings.map((warning) => (
          <li key={warning}>{warning}</li>
        ))}
      </ul>
      <h4>Invalidation Conditions</h4>
      <ul className="stack-list">
        {invalidationConditions.map((condition) => (
          <li key={condition}>{condition}</li>
        ))}
      </ul>
    </Card>
  );
}
