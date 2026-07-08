# AlphaCouncil

AlphaCouncil is a multi-agent global equity trading decision platform for research, signal review, risk control, historical backtesting, and decision logging.

This MVP includes a FastAPI backend, React + Vite frontend, SQLite-backed decision history, deterministic mock data, market status logic, and an optional yfinance market-data provider.



## MVP Boundary

AlphaCouncil is research support only.

- No live trading.
- No broker integration.
- No paper trading.
- No real API keys.
- No paid market data requirement.
- No recommendation is guaranteed.

The app generates research decisions only: `BUY`, `SELL`, `HOLD`, `WATCH`, and `AVOID`.

## Architecture Summary

The backend exposes `/api/v1` endpoints through FastAPI. The data provider layer can use deterministic mock data or optional yfinance market data. The Decision Committee combines agent outputs, applies Risk Manager veto rules, saves the final decision to SQLite, and returns a structured response to the frontend.

The frontend is a lightweight React/Vite app with:

- Dashboard
- Stock Analysis
- Watchlist
- Backtest runner and history
- Decision Evaluation
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

`requirements.txt` includes `yfinance`, so the same install command prepares both mock mode and optional yfinance mode.

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
| GET | `/api/v1/data-sources/status` | Active data provider and quality warning. |
| GET | `/api/v1/watchlist` | List saved watchlist items. |
| GET | `/api/v1/watchlist/summary` | Lightweight watchlist risk review. |
| POST | `/api/v1/watchlist` | Add a watchlist item. |
| GET | `/api/v1/watchlist/{id}` | Read one watchlist item. |
| PATCH | `/api/v1/watchlist/{id}` | Update watchlist metadata. |
| DELETE | `/api/v1/watchlist/{id}` | Remove a watchlist item. |
| POST | `/api/v1/analysis/run` | Run multi-agent analysis with the selected data provider and save the decision. |
| GET | `/api/v1/decisions` | List saved decisions from SQLite. |
| GET | `/api/v1/decisions/{decision_id}` | Inspect one saved decision payload. |
| POST | `/api/v1/backtests/run` | Run a single-ticker long-only historical backtest. |
| GET | `/api/v1/backtests` | List saved backtest runs from SQLite. |
| GET | `/api/v1/backtests/{backtest_id}` | Inspect one saved backtest result. |
| POST | `/api/v1/evaluations/decision/{decision_id}` | Evaluate one saved decision. |
| POST | `/api/v1/evaluations/run` | Evaluate eligible saved decisions. |
| GET | `/api/v1/evaluations` | List saved decision evaluations with filters. |
| GET | `/api/v1/evaluations/summary` | Aggregate decision evaluation analytics. |
| GET | `/api/v1/evaluations/{evaluation_id}` | Inspect one saved evaluation payload. |

Example analysis request:

```json
{
  "ticker": "NVDA",
  "market": "US",
  "time_horizon": "swing",
  "strategy_preference": "moving_average_crossover"
}
```

Example backtest request:

```json
{
  "ticker": "NVDA",
  "market": "US",
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "strategy_name": "moving_average_crossover",
  "initial_capital": 100000,
  "transaction_cost_bps": 5,
  "slippage_bps": 10
}
```

Backtest results always include:

```text
Historical simulation only. Past performance does not guarantee future results.
```

Decision evaluation results always include:

```text
Decision evaluation is historical and observational only. It does not prove future profitability.
```

## Environment Variables

Copy `backend/.env.example` to `backend/.env` for local development:

```text
APP_ENV=development
DATABASE_URL=sqlite:///./alphacouncil.db
DATA_PROVIDER=mock
ENABLE_LIVE_TRADING=false
```

Provider options:

```text
DATA_PROVIDER=mock
DATA_PROVIDER=yfinance
```

Ticker examples for yfinance mode:

| Market | Examples |
| --- | --- |
| US | `NVDA`, `AAPL`, `TSLA` |
| Japan | `7203` or `7203.T` |
| Taiwan | `2330` or `2330.TW` |
| Korea | `005930` or `005930.KS` |

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

AlphaCouncil may use deterministic mock data or yfinance market data depending on `DATA_PROVIDER`. yfinance data may be delayed, incomplete, adjusted, or unavailable and is not suitable for guaranteed trading decisions. AlphaCouncil is not financial advice, does not guarantee outcomes, and does not execute trades. Always verify market data, liquidity, risk, and suitability independently before making investment decisions.
