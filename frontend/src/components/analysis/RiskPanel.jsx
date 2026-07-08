import { useTranslation } from "react-i18next";

import Card from "../ui/Card.jsx";

export default function RiskPanel({ warnings = [], invalidationConditions = [] }) {
  const { t } = useTranslation();

  return (
    <Card>
      <h3>{t("riskPanel.riskReview")}</h3>
      <ul className="stack-list">
        {warnings.map((warning) => (
          <li key={warning}>{warning}</li>
        ))}
      </ul>
      <h4>{t("riskPanel.invalidationConditions")}</h4>
      <ul className="stack-list">
        {invalidationConditions.map((condition) => (
          <li key={condition}>{condition}</li>
        ))}
      </ul>
    </Card>
  );
}
