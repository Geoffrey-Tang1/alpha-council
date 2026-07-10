import { useTranslation } from "react-i18next";

export default function BrandLockup() {
  const { t } = useTranslation();

  return (
    <div className="brand-lockup" aria-label={t("app.name")}>
      <div className="brand-mark" aria-hidden="true">
        <span className="brand-compass" />
      </div>
      <div className="brand-text">
        <h1>{t("app.name")}</h1>
        <span className="brand-short">{t("app.shortName")}</span>
      </div>
    </div>
  );
}
