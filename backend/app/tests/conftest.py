import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path("test_alphacouncil.db")
if TEST_DB.exists():
    TEST_DB.unlink()

TEST_LLM_SETTINGS = Path("test_llm_settings.local.json")
if TEST_LLM_SETTINGS.exists():
    TEST_LLM_SETTINGS.unlink()

TEST_MODEL_CACHE = Path("test_model_catalog_cache.local.json")
if TEST_MODEL_CACHE.exists():
    TEST_MODEL_CACHE.unlink()

os.environ["DATABASE_URL"] = "sqlite:///./test_alphacouncil.db"
os.environ["DATA_PROVIDER"] = "mock"
os.environ["FINANCIAL_DATA_PROVIDER"] = "auto"
os.environ["FINANCIAL_DATA_CACHE_ENABLED"] = "true"
os.environ["NEWS_RESEARCH_PROVIDER"] = "auto"
os.environ["ENABLE_LIVE_TRADING"] = "false"
os.environ["LLM_PROVIDER"] = "disabled"
os.environ["ENABLE_LLM_REASONING"] = "false"
os.environ["OPENAI_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["LLM_SETTINGS_PATH"] = str(TEST_LLM_SETTINGS)
os.environ["LLM_MODEL_CACHE_PATH"] = str(TEST_MODEL_CACHE)

from app.main import app  # noqa: E402
from app.financial_data.cache import GLOBAL_FINANCIAL_DATA_CACHE  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def isolate_llm_settings_file():
    GLOBAL_FINANCIAL_DATA_CACHE.clear()
    if TEST_LLM_SETTINGS.exists():
        TEST_LLM_SETTINGS.unlink()
    if TEST_MODEL_CACHE.exists():
        TEST_MODEL_CACHE.unlink()
    yield
    GLOBAL_FINANCIAL_DATA_CACHE.clear()
    if TEST_LLM_SETTINGS.exists():
        TEST_LLM_SETTINGS.unlink()
    if TEST_MODEL_CACHE.exists():
        TEST_MODEL_CACHE.unlink()
