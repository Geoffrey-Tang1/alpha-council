from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, decisions, health, market_status, watchlist
from app.core.config import settings
from app.db.database import initialize_database


def create_app() -> FastAPI:
    initialize_database()
    app = FastAPI(
        title="AlphaCouncil API",
        version=settings.version,
        description="Research-only multi-agent equity decision support API. No live trading.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(market_status.router, prefix="/api/v1")
    app.include_router(analysis.router, prefix="/api/v1")
    app.include_router(decisions.router, prefix="/api/v1")
    app.include_router(watchlist.router, prefix="/api/v1")
    return app


app = create_app()
