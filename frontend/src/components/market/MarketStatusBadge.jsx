import { useTranslation } from "react-i18next";

import { enumLabel } from "../../utils/labels.js";
import Badge from "../ui/Badge.jsx";

export default function MarketStatusBadge({ status }) {
  const { t } = useTranslation();
  const tone = status === "OPEN" ? "success" : status === "UNKNOWN" ? "warning" : "neutral";
  return <Badge tone={tone}>{enumLabel(t, status)}</Badge>;
}
