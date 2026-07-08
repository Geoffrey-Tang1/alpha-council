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
    llm_provider: str = os.getenv("LLM_PROVIDER", "disabled")
    enable_llm_reasoning: bool = os.getenv("ENABLE_LLM_REASONING", "false").lower() == "true"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    version: str = "0.1.0"


settings = Settings()
