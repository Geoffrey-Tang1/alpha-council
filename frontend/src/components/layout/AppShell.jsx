import { useEffect, useState } from "react";

import { getDataSourceStatus } from "../../api/client.js";
import Button from "../ui/Button.jsx";

export default function AppShell({ currentPage, onNavigate, children }) {
  const [dataSourceStatus, setDataSourceStatus] = useState(null);
  const navItems = [
    ["dashboard", "Dashboard"],
    ["analysis", "Stock Analysis"],
    ["watchlist", "Watchlist"],
    ["backtest", "Backtest"],
    ["evaluations", "Decision Evaluation"],
    ["decisions", "Decision Log"]
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
      ? "Data provider: yfinance. Data may be delayed or incomplete."
      : "MVP Mode: using mock data. Not real market data.";
  const bannerClass = dataSourceStatus?.data_provider === "yfinance" ? "mock-banner provider-banner" : "mock-banner";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Research desk</p>
          <h1>AlphaCouncil</h1>
        </div>
        <nav className="nav-list" aria-label="Primary navigation">
          {navItems.map(([page, label]) => (
            <Button key={page} className={currentPage === page ? "active" : ""} onClick={() => onNavigate(page)}>
              {label}
            </Button>
          ))}
        </nav>
        <p className="sidebar-note">MVP research support only. No live trading.</p>
      </aside>
      <main className="content">
        <div className={bannerClass}>{bannerText}</div>
        {children}
      </main>
    </div>
  );
}
