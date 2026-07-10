import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_ROOT = REPO_ROOT / "frontend"


def test_openapi_uses_wisoka_compass_public_name(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    body = response.json()
    assert body["info"]["title"] == "Wisoka Compass API"
    assert "AlphaCouncil" not in body["info"]["title"]


def test_browser_metadata_and_locales_use_wisoka_compass():
    index_html = (FRONTEND_ROOT / "index.html").read_text()
    assert "<title>Wisoka Compass</title>" in index_html
    assert "AlphaCouncil" not in index_html

    for locale_path in (FRONTEND_ROOT / "src/i18n/locales").glob("*.json"):
        locale = json.loads(locale_path.read_text())
        assert locale["app"]["name"] == "Wisoka Compass"
        assert locale["app"]["shortName"] == "Wisoka"
        assert "AlphaCouncil" not in json.dumps(locale, ensure_ascii=False)


def test_legacy_persistence_and_api_keys_are_intentionally_preserved():
    i18n_index = (FRONTEND_ROOT / "src/i18n/index.js").read_text()
    config = (REPO_ROOT / "backend/app/core/config.py").read_text()
    health = (REPO_ROOT / "backend/app/api/routes/health.py").read_text()

    assert "alphacouncil.language" in i18n_index
    assert "alphacouncil.db" in config
    assert "alphacouncil-api" in health
