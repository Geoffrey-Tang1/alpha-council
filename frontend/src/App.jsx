import { useState } from "react";

import AppShell from "./components/layout/AppShell.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import DecisionLogPage from "./pages/DecisionLogPage.jsx";
import StockAnalysisPage from "./pages/StockAnalysisPage.jsx";

export default function App() {
  const [page, setPage] = useState("dashboard");

  return (
    <AppShell currentPage={page} onNavigate={setPage}>
      {page === "dashboard" && <DashboardPage onNavigate={setPage} />}
      {page === "analysis" && <StockAnalysisPage />}
      {page === "decisions" && <DecisionLogPage />}
    </AppShell>
  );
}
