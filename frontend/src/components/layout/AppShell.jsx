import Button from "../ui/Button.jsx";

export default function AppShell({ currentPage, onNavigate, children }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Research desk</p>
          <h1>AlphaCouncil</h1>
        </div>
        <nav className="nav-list" aria-label="Primary navigation">
          <Button className={currentPage === "dashboard" ? "active" : ""} onClick={() => onNavigate("dashboard")}>
            Dashboard
          </Button>
          <Button className={currentPage === "analysis" ? "active" : ""} onClick={() => onNavigate("analysis")}>
            Stock Analysis
          </Button>
          <Button className={currentPage === "decisions" ? "active" : ""} onClick={() => onNavigate("decisions")}>
            Decision Log
          </Button>
        </nav>
        <p className="sidebar-note">MVP research support only. No live trading.</p>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
