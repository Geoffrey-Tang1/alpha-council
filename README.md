# AlphaCouncil

AlphaCouncil is a multi-agent global equity trading decision platform for research, signal review, risk control, backtesting preparation, and decision logging.

This Phase 1 MVP is a clean local skeleton. It includes a FastAPI backend, React + Vite frontend, SQLite-backed decision history, deterministic mock data, market status logic, and a mock multi-agent analysis workflow.

Suggested repository name: `alpha-council`

## MVP Boundary

AlphaCouncil Phase 1 is research support only.

- No live trading.
- No broker integration.
- No paper trading.
- No real API keys.
- No paid market data requirement.
- No recommendation is guaranteed.

The app generates research decisions only: `BUY`, `SELL`, `HOLD`, `WATCH`, and `AVOID`.

## Architecture Summary

The backend exposes `/api/v1` endpoints through FastAPI. A mock data provider feeds deterministic price, company, news, fundamentals, and macro data into the agent workflow. The Decision Committee combines agent outputs, applies Risk Manager veto rules, saves the final decision to SQLite, and returns a structured response to the frontend.

The frontend is a lightweight React/Vite app with:

- Dashboard
- Stock Analysis
- Watchlist
- Backtest form shell
- Decision Log
- Decision Detail payload inspection

## macOS Prerequisites

Install these before running the app:

- macOS
- zsh
- Python 3.11 or newer
- Node.js 20 or newer
- npm
- Git

## Backend Setup

```bash
cd ~/Projects/AlphaCouncil/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run Backend

```bash
cd ~/Projects/AlphaCouncil/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Backend URL:

```text
http://localhost:8000
```

## Frontend Setup

```bash
cd ~/Projects/AlphaCouncil/frontend
npm install
```

## Run Frontend

```bash
cd ~/Projects/AlphaCouncil/frontend
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

## Run Backend Tests

```bash
cd ~/Projects/AlphaCouncil/backend
source .venv/bin/activate
pytest
```

## Stop Servers

In each terminal running a server:

```bash
Ctrl+C
```

If ports are stuck on macOS:

```bash
lsof -i :8000
kill -9 <PID>
lsof -i :5173
kill -9 <PID>
```

## API Endpoint Summary

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Backend health check. |
| GET | `/api/v1/market-status` | US, JP, TW, and KR market status. |
| GET | `/api/v1/watchlist` | List saved watchlist items. |
| POST | `/api/v1/watchlist` | Add a watchlist item. |
| GET | `/api/v1/watchlist/{id}` | Read one watchlist item. |
| PATCH | `/api/v1/watchlist/{id}` | Update watchlist metadata. |
| DELETE | `/api/v1/watchlist/{id}` | Remove a watchlist item. |
| POST | `/api/v1/analysis/run` | Run deterministic mock multi-agent analysis and save the decision. |
| GET | `/api/v1/decisions` | List saved decisions from SQLite. |
| GET | `/api/v1/decisions/{decision_id}` | Inspect one saved decision payload. |

Example analysis request:

```json
{
  "ticker": "NVDA",
  "market": "US",
  "time_horizon": "swing",
  "strategy_preference": "moving_average_crossover"
}
```

## Environment Variables

Copy `backend/.env.example` to `backend/.env` for local development:

```text
APP_ENV=development
DATABASE_URL=sqlite:///./alphacouncil.db
DATA_PROVIDER=mock
ENABLE_LIVE_TRADING=false
```

Do not commit `.env`.

## macOS Troubleshooting

| Problem | Fix |
| --- | --- |
| `python3` not found | Install Python 3.11+ and reopen your terminal. |
| Virtual environment not active | Run `source .venv/bin/activate` from `~/Projects/AlphaCouncil/backend`. |
| `pip install` fails | Confirm the virtual environment is active and Python is 3.11+. |
| `npm` not found | Install Node.js 20+ and reopen your terminal. |
| Backend port is busy | Run `lsof -i :8000`, then `kill -9 <PID>`. |
| Frontend port is busy | Run `lsof -i :5173`, then `kill -9 <PID>`. |
| Frontend cannot reach API | Confirm backend is running on `http://localhost:8000`. |
| SQLite database looks stale | Stop the backend and remove `backend/alphacouncil.db` if you want a fresh local database. |

## Risk Disclaimer

AlphaCouncil Phase 1 uses mock data and deterministic placeholder logic. It is not financial advice, does not guarantee outcomes, and does not execute trades. Always verify market data, liquidity, risk, and suitability independently before making investment decisions.
