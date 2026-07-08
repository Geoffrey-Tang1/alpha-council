import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getDataSourceStatus } from "../../api/client.js";
import Button from "../ui/Button.jsx";
import LanguageSwitcher from "./LanguageSwitcher.jsx";

export default function AppShell({ currentPage, onNavigate, children }) {
  const { t } = useTranslation();
  const [dataSourceStatus, setDataSourceStatus] = useState(null);
  const navItems = [
    ["dashboard", "sidebar.nav.dashboard"],
    ["analysis", "sidebar.nav.analysis"],
    ["watchlist", "sidebar.nav.watchlist"],
    ["backtest", "sidebar.nav.backtest"],
    ["evaluations", "sidebar.nav.evaluations"],
    ["decisions", "sidebar.nav.decisions"]
  ];

  useEffect(() => {
    getDataSourceStatus()
      .then(setDataSourceStatus)
      .catch(() => {
        setDataSourceStatus({
          data_provider: "mock",
          data_quality: "MOCK",
          data_disclaimer: "MVP Mode: using mock data. Not real market data."
        });
      });
  }, []);

  const bannerText =
    dataSourceStatus?.data_provider === "yfinance"
      ? t("banner.yfinance")
      : t("banner.mock");
  const bannerClass = dataSourceStatus?.data_provider === "yfinance" ? "mock-banner provider-banner" : "mock-banner";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">{t("sidebar.researchDesk")}</p>
          <h1>{t("app.name")}</h1>
        </div>
        <LanguageSwitcher />
        <nav className="nav-list" aria-label={t("sidebar.navigation")}>
          {navItems.map(([page, labelKey]) => (
            <Button key={page} className={currentPage === page ? "active" : ""} onClick={() => onNavigate(page)}>
              {t(labelKey)}
            </Button>
          ))}
        </nav>
        <p className="sidebar-note">{t("sidebar.note")}</p>
      </aside>
      <main className="content">
        <div className={bannerClass}>{bannerText}</div>
        {children}
      </main>
    </div>
  );
}
