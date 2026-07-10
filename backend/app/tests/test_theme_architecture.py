import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_ROOT = REPO_ROOT / "frontend"


def test_theme_initializes_before_react_with_dark_default():
    index_html = (FRONTEND_ROOT / "index.html").read_text()

    assert '<html lang="en" data-theme="dark">' in index_html
    assert 'var storageKey = "wisoka.appearance";' in index_html
    assert 'var defaultPreference = "dark";' in index_html
    assert 'prefers-color-scheme: dark' in index_html
    assert "document.documentElement.dataset.theme = resolvedTheme" in index_html
    assert 'meta name="theme-color"' in index_html
    assert index_html.index("wisoka.appearance") < index_html.index('<script type="module" src="/src/main.jsx">')


def test_theme_controller_preserves_existing_storage_keys():
    appearance_source = (FRONTEND_ROOT / "src/theme/appearance.js").read_text()
    provider_source = (FRONTEND_ROOT / "src/theme/ThemeProvider.jsx").read_text()
    i18n_source = (FRONTEND_ROOT / "src/i18n/index.js").read_text()

    assert 'APPEARANCE_STORAGE_KEY = "wisoka.appearance"' in appearance_source
    assert 'DEFAULT_APPEARANCE = "dark"' in appearance_source
    assert '["dark", "light", "system"]' in appearance_source
    assert 'window.matchMedia("(prefers-color-scheme: dark)")' in provider_source
    assert "addEventListener" in provider_source
    assert "removeEventListener" in provider_source
    assert "alphacouncil.language" in i18n_source


def test_theme_tokens_include_light_and_preserve_financial_semantics():
    css = (FRONTEND_ROOT / "src/styles/global.css").read_text()

    assert ':root[data-theme="light"]' in css
    assert "--color-brand-primary: #2F80ED;" in css
    assert "--color-brand-primary: #236FC5;" in css
    assert "--color-positive: #2FC98F;" in css
    assert "--color-positive: #16855E;" in css
    assert "--color-negative: #F06472;" in css
    assert "--color-negative: #C84150;" in css
    assert "--color-warning: #F3B94F;" in css
    assert "--color-warning: #A96A0A;" in css
    assert "--color-chart-bg:" in css
    assert "--color-chart-grid:" in css
    assert "scrollbar-color:" in css


def test_appearance_locale_strings_exist_for_all_supported_languages():
    required_keys = {
        "title",
        "subtitle",
        "light",
        "dark",
        "system",
        "followSystem",
        "currentlyLight",
        "currentlyDark",
    }

    for locale_path in (FRONTEND_ROOT / "src/i18n/locales").glob("*.json"):
        locale = json.loads(locale_path.read_text())
        assert required_keys.issubset(locale["appearance"].keys())
