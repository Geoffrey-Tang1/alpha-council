import Card from "../ui/Card.jsx";

export default function AgentOpinionCard({ title, items = [], secondary = [] }) {
  return (
    <Card>
      <h3>{title}</h3>
      <ul className="stack-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      {secondary.length > 0 && (
        <div className="subtle-list">
          {secondary.map((item) => (
            <p key={item}>{item}</p>
          ))}
        </div>
      )}
    </Card>
  );
}
