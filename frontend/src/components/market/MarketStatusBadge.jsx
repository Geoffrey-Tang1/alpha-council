import Badge from "../ui/Badge.jsx";

export default function MarketStatusBadge({ status }) {
  const tone = status === "OPEN" ? "success" : status === "UNKNOWN" ? "warning" : "neutral";
  return <Badge tone={tone}>{status}</Badge>;
}
