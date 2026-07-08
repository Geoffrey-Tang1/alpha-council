import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path("test_alphacouncil.db")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = "sqlite:///./test_alphacouncil.db"
os.environ["DATA_PROVIDER"] = "mock"
os.environ["ENABLE_LIVE_TRADING"] = "false"
os.environ["LLM_PROVIDER"] = "disabled"
os.environ["ENABLE_LLM_REASONING"] = "false"
os.environ["OPENAI_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)
