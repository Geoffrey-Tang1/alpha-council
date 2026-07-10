import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { getLlmSettings, testLlmConnection, updateLlmSettings } from "../api/client.js";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";

const PROVIDERS = [
  "disabled",
  "mock",
  "openai",
  "anthropic",
  "gemini",
  "deepseek",
  "xai",
  "mistral",
  "groq",
  "openrouter",
  "ollama",
  "custom_openai_compatible"
];

const MODEL_OPTIONS = {
  disabled: ["none"],
  mock: ["mock-llm-v1"],
  openai: ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini", "gpt-4o"],
  anthropic: ["claude-3-5-haiku-latest", "claude-3-5-sonnet-latest", "claude-3-7-sonnet-latest"],
  gemini: ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
  deepseek: ["deepseek-chat", "deepseek-reasoner"],
  xai: ["grok-2", "grok-2-mini"],
  mistral: ["mistral-small-latest", "mistral-large-latest"],
  groq: ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"],
  openrouter: ["openrouter/auto"],
  ollama: ["llama3.1", "qwen2.5", "mistral"],
  custom_openai_compatible: ["custom-model"]
};

const BASE_URL_PROVIDERS = new Set([
  "openrouter",
  "ollama",
  "custom_openai_compatible",
  "deepseek",
  "groq",
  "mistral"
]);

const CUSTOM_MODEL_PROVIDERS = new Set(["openrouter", "ollama", "custom_openai_compatible"]);
const API_KEY_HIDDEN_PROVIDERS = new Set(["disabled", "mock", "ollama"]);

const initialForm = {
  llm_provider: "disabled",
  enable_llm_reasoning: false,
  selected_model: "none",
  base_url: "",
  temperature: 0.2,
  max_tokens: 1200,
  timeout_seconds: 30
};

function providerLabel(t, provider) {
  return t(`settings.providers.${provider}`, { defaultValue: provider });
}

function statusTone(status) {
  if (status === "success") return "success";
  if (status === "failed") return "danger";
  return "neutral";
}

export default function SettingsPage() {
  const { t } = useTranslation();
  const [settings, setSettings] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [apiKeyDraft, setApiKeyDraft] = useState("");
  const [apiKeyChanged, setApiKeyChanged] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const modelOptions = useMemo(
    () => MODEL_OPTIONS[form.llm_provider] || ["custom-model"],
    [form.llm_provider]
  );
  const showApiKey = !API_KEY_HIDDEN_PROVIDERS.has(form.llm_provider);
  const showBaseUrl = BASE_URL_PROVIDERS.has(form.llm_provider);
  const showCustomModel = CUSTOM_MODEL_PROVIDERS.has(form.llm_provider);
  const providerIsDisabled = form.llm_provider === "disabled";

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    setLoading(true);
    setError("");
    try {
      const response = await getLlmSettings();
      applySettings(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function applySettings(response) {
    setSettings(response);
    setForm({
      llm_provider: response.llm_provider,
      enable_llm_reasoning: response.enable_llm_reasoning,
      selected_model: response.selected_model,
      base_url: response.base_url || "",
      temperature: response.temperature,
      max_tokens: response.max_tokens,
      timeout_seconds: response.timeout_seconds
    });
    setApiKeyDraft("");
    setApiKeyChanged(false);
  }

  function updateField(event) {
    const { name, value, checked, type } = event.target;
    setForm((current) => {
      const nextValue = type === "checkbox" ? checked : value;
      return { ...current, [name]: nextValue };
    });
  }

  function updateProvider(event) {
    const provider = event.target.value;
    setForm((current) => ({
      ...current,
      llm_provider: provider,
      enable_llm_reasoning: provider === "disabled" ? false : current.enable_llm_reasoning,
      selected_model: MODEL_OPTIONS[provider]?.[0] || "custom-model",
      base_url: provider === "ollama" ? "http://localhost:11434" : current.base_url
    }));
  }

  function updateReasoningToggle(event) {
    setForm((current) => ({
      ...current,
      enable_llm_reasoning: event.target.checked
    }));
  }

  function updateApiKey(event) {
    setApiKeyDraft(event.target.value);
    setApiKeyChanged(true);
  }

  function buildPayload(includeApiKey) {
    const payload = {
      ...form,
      base_url: form.base_url || null,
      temperature: Number(form.temperature),
      max_tokens: Number(form.max_tokens),
      timeout_seconds: Number(form.timeout_seconds)
    };
    if (includeApiKey) {
      payload.api_key = apiKeyDraft;
    }
    return payload;
  }

  async function saveSettings(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const response = await updateLlmSettings(buildPayload(apiKeyChanged));
      applySettings(response);
      setMessage(t("settings.saved"));
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function testConnection() {
    setTesting(true);
    setError("");
    setMessage("");
    try {
      const response = await testLlmConnection({
        llm_provider: form.llm_provider,
        selected_model: form.selected_model,
        api_key: apiKeyChanged ? apiKeyDraft : null,
        base_url: form.base_url || null
      });
      setMessage(response.message);
      await loadSettings();
    } catch (err) {
      setError(err.message);
    } finally {
      setTesting(false);
    }
  }

  async function resetDisabled() {
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const response = await updateLlmSettings({
        llm_provider: "disabled",
        enable_llm_reasoning: false,
        selected_model: "none",
        api_key: "",
        base_url: null,
        temperature: 0.2,
        max_tokens: 1200,
        timeout_seconds: 30
      });
      applySettings(response);
      setMessage(t("settings.resetComplete"));
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">{t("settings.eyebrow")}</p>
          <h2>{t("settings.title")}</h2>
          <p>{t("settings.subtitle")}</p>
        </div>
      </div>

      {error && <Card className="error-card">{error}</Card>}
      {message && <Card className="success-card">{message}</Card>}

      <div className="settings-grid">
        <Card>
          <h3>{t("settings.llmConfiguration")}</h3>
          <form className="settings-form" onSubmit={saveSettings}>
            <label className={`toggle-field ${providerIsDisabled ? "is-disabled" : ""}`}>
              <input
                name="enable_llm_reasoning"
                type="checkbox"
                checked={Boolean(form.enable_llm_reasoning)}
                onChange={updateReasoningToggle}
                disabled={providerIsDisabled}
              />
              <span>{t("settings.enableLlmReasoning")}</span>
            </label>
            {providerIsDisabled && <p className="toggle-help">{t("settings.chooseProviderHelp")}</p>}

            <div className="settings-form-grid">
              <label>
                {t("settings.provider")}
                <select name="llm_provider" value={form.llm_provider} onChange={updateProvider} disabled={loading}>
                  {PROVIDERS.map((provider) => (
                    <option key={provider} value={provider}>
                      {providerLabel(t, provider)}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                {t("settings.model")}
                <select
                  value={modelOptions.includes(form.selected_model) ? form.selected_model : "__custom"}
                  onChange={(event) => {
                    const value = event.target.value;
                    setForm((current) => ({
                      ...current,
                      selected_model: value === "__custom" ? current.selected_model : value
                    }));
                  }}
                >
                  {modelOptions.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                  {showCustomModel && <option value="__custom">{t("settings.customModel")}</option>}
                </select>
              </label>

              {showCustomModel && (
                <label>
                  {t("settings.customModel")}
                  <input
                    name="selected_model"
                    value={form.selected_model}
                    onChange={updateField}
                    placeholder={t("settings.customModelPlaceholder")}
                  />
                </label>
              )}

              {showBaseUrl && (
                <label>
                  {t("settings.baseUrl")}
                  <input
                    name="base_url"
                    value={form.base_url}
                    onChange={updateField}
                    placeholder={form.llm_provider === "ollama" ? "http://localhost:11434" : "https://api.example.com/v1"}
                  />
                </label>
              )}

              {showApiKey && (
                <label>
                  {t("settings.apiKey")}
                  <input
                    name="api_key"
                    type="password"
                    value={apiKeyDraft}
                    onChange={updateApiKey}
                    placeholder={settings?.masked_api_key || t("settings.leaveBlank")}
                    autoComplete="off"
                  />
                </label>
              )}

              <label>
                {t("settings.temperature")}
                <input name="temperature" type="number" min="0" max="2" step="0.1" value={form.temperature} onChange={updateField} />
              </label>

              <label>
                {t("settings.maxTokens")}
                <input name="max_tokens" type="number" min="128" max="8000" step="1" value={form.max_tokens} onChange={updateField} />
              </label>

              <label>
                {t("settings.timeoutSeconds")}
                <input
                  name="timeout_seconds"
                  type="number"
                  min="5"
                  max="120"
                  step="1"
                  value={form.timeout_seconds}
                  onChange={updateField}
                />
              </label>
            </div>

            <p className="muted">{t("settings.keyStorageHelp")}</p>
            <p className="data-disclaimer">{t("settings.noCommitWarning")}</p>

            <div className="form-button-row">
              <Button type="submit" disabled={saving || loading}>
                {saving ? t("settings.saving") : t("settings.saveSettings")}
              </Button>
              <Button type="button" onClick={testConnection} disabled={testing || loading}>
                {testing ? t("settings.testing") : t("settings.testConnection")}
              </Button>
              <Button type="button" onClick={resetDisabled} disabled={saving || loading}>
                {t("settings.resetDisabled")}
              </Button>
            </div>
          </form>
        </Card>

        <Card>
          <div className="card-row">
            <h3>{t("settings.currentStatus")}</h3>
            <Badge tone={statusTone(settings?.last_connection_status)}>{settings?.last_connection_status || "not_tested"}</Badge>
          </div>
          <dl className="detail-list">
            <div>
              <dt>{t("settings.currentProvider")}</dt>
              <dd>{providerLabel(t, settings?.llm_provider || "disabled")}</dd>
            </div>
            <div>
              <dt>{t("settings.llmEnabled")}</dt>
              <dd>{settings?.enable_llm_reasoning ? t("llm.yes") : t("llm.no")}</dd>
            </div>
            <div>
              <dt>{t("settings.model")}</dt>
              <dd>{settings?.selected_model || "none"}</dd>
            </div>
            <div>
              <dt>{t("settings.apiKeyPresent")}</dt>
              <dd>{settings?.api_key_present ? t("llm.yes") : t("llm.no")}</dd>
            </div>
            <div>
              <dt>{t("settings.maskedApiKey")}</dt>
              <dd>{settings?.masked_api_key || "N/A"}</dd>
            </div>
            <div>
              <dt>{t("settings.connectionStatus")}</dt>
              <dd>{settings?.last_connection_status || "not_tested"}</dd>
            </div>
            <div>
              <dt>{t("settings.connectionMessage")}</dt>
              <dd>{settings?.last_connection_message || ""}</dd>
            </div>
          </dl>
        </Card>
      </div>
    </div>
  );
}
