import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./alphacouncil.db")
    data_provider: str = os.getenv("DATA_PROVIDER", "mock")
    enable_live_trading: bool = os.getenv("ENABLE_LIVE_TRADING", "false").lower() == "true"
    version: str = "0.1.0"


settings = Settings()
