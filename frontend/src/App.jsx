import { useState } from "react";

import AppShell from "./components/layout/AppShell.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import BacktestPage from "./pages/BacktestPage.jsx";
import DecisionDetailPage from "./pages/DecisionDetailPage.jsx";
import DecisionLogPage from "./pages/DecisionLogPage.jsx";
import StockAnalysisPage from "./pages/StockAnalysisPage.jsx";
import WatchlistPage from "./pages/WatchlistPage.jsx";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [selectedDecisionId, setSelectedDecisionId] = useState(null);

  function navigate(nextPage) {
    setPage(nextPage);
    if (nextPage !== "decisionDetail") {
      setSelectedDecisionId(null);
    }
  }

  function openDecision(decisionId) {
    setSelectedDecisionId(decisionId);
    setPage("decisionDetail");
  }

  return (
    <AppShell currentPage={page} onNavigate={navigate}>
      {page === "dashboard" && <DashboardPage onNavigate={navigate} onSelectDecision={openDecision} />}
      {page === "analysis" && <StockAnalysisPage />}
      {page === "watchlist" && <WatchlistPage onNavigate={navigate} />}
      {page === "backtest" && <BacktestPage />}
      {page === "decisions" && <DecisionLogPage onSelectDecision={openDecision} />}
      {page === "decisionDetail" && (
        <DecisionDetailPage decisionId={selectedDecisionId} onBack={() => navigate("decisions")} />
      )}
    </AppShell>
  );
}
