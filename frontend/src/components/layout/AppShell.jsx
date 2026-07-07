import Button from "../ui/Button.jsx";

export default function AppShell({ currentPage, onNavigate, children }) {
  const navItems = [
    ["dashboard", "Dashboard"],
    ["analysis", "Stock Analysis"],
    ["watchlist", "Watchlist"],
    ["backtest", "Backtest"],
    ["decisions", "Decision Log"]
  ];

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
        <div className="mock-banner">MVP Mode: using mock data. Not real market data.</div>
        {children}
      </main>
    </div>
  );
}
