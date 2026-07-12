import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  getFinancialDataStatus,
  getLlmModels,
  getLlmSettings,
  getNewsResearchStatus,
  refreshLlmModels,
  testLlmConnection,
  updateLlmSettings
} from "../api/client.js";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { APPEARANCE_OPTIONS } from "../theme/appearance.js";
import { useTheme } from "../theme/ThemeProvider.jsx";

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

const BASE_URL_PROVIDERS = new Set([
  "openrouter",
  "ollama",
  "custom_openai_compatible",
  "deepseek",
  "groq",
  "mistral"
]);

const API_KEY_HIDDEN_PROVIDERS = new Set(["disabled", "mock", "ollama"]);
const CUSTOM_MODEL_VALUE = "__custom";

const DEFAULT_BASE_URLS = {
  openrouter: "https://openrouter.ai/api/v1",
  ollama: "http://localhost:11434",
  custom_openai_compatible: "",
  deepseek: "https://api.deepseek.com/v1",
  groq: "https://api.groq.com/openai/v1",
  mistral: "https://api.mistral.ai/v1"
};

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
  if (status === "missing_api_key" || status === "error" || status === "unavailable") return "warning";
  return "neutral";
}

function defaultModelFor(provider, models) {
  if (provider === "disabled") {
    return "none";
  }
  return models[0]?.id || "custom-model";
}

export default function SettingsPage() {
  const { t } = useTranslation();
  const { appearancePreference, resolvedTheme, systemPrefersDark, setAppearancePreference } = useTheme();
  const [settings, setSettings] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [apiKeyDraft, setApiKeyDraft] = useState("");
  const [apiKeyChanged, setApiKeyChanged] = useState(false);
  const [customModel, setCustomModel] = useState("");
  const [modelCatalog, setModelCatalog] = useState(null);
  const [financialStatus, setFinancialStatus] = useState(null);
  const [newsResearchStatus, setNewsResearchStatus] = useState(null);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsRefreshing, setModelsRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const modelOptions = useMemo(() => modelCatalog?.models || [], [modelCatalog]);
  const modelIds = useMemo(() => modelOptions.map((model) => model.id), [modelOptions]);
  const showApiKey = !API_KEY_HIDDEN_PROVIDERS.has(form.llm_provider);
  const showBaseUrl = BASE_URL_PROVIDERS.has(form.llm_provider);
  const providerIsDisabled = form.llm_provider === "disabled";
  const modelSelectValue = providerIsDisabled ? "none" : modelIds.includes(form.selected_model) ? form.selected_model : CUSTOM_MODEL_VALUE;
  const showCustomModel = !providerIsDisabled && modelSelectValue === CUSTOM_MODEL_VALUE;

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    setLoading(true);
    setError("");
    try {
      const response = await getLlmSettings();
      applySettings(response);
      await loadModelCatalog(response.llm_provider, response.selected_model, false);
      await loadFinancialStatus();
      await loadNewsResearchStatus();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadFinancialStatus() {
    try {
      const response = await getFinancialDataStatus();
      setFinancialStatus(response);
    } catch (err) {
      setFinancialStatus({
        provider: "unknown",
        availability_status: "failed",
        freshness_status: "unknown",
        warnings: [err.message],
        capabilities: [],
        cache: {}
      });
    }
  }

  async function loadNewsResearchStatus() {
    try {
      const response = await getNewsResearchStatus();
      setNewsResearchStatus(response);
    } catch (err) {
      setNewsResearchStatus({
        provider: "unknown",
        enabled: false,
        supports_live_news: false,
        supports_sentiment: false,
        cache_status: {},
        warnings: [err.message],
        unavailable_reasons: [err.message]
      });
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

  async function loadModelCatalog(provider, preferredModel = null, updateSelectedModel = true) {
    setModelsLoading(true);
    try {
      const catalog = await getLlmModels(provider);
      applyModelCatalog(catalog, preferredModel, updateSelectedModel);
    } catch (err) {
      setError(err.message);
    } finally {
      setModelsLoading(false);
    }
  }

  function applyModelCatalog(catalog, preferredModel = null, updateSelectedModel = true) {
    setModelCatalog(catalog);
    const ids = (catalog.models || []).map((model) => model.id);
    const nextModel = preferredModel || defaultModelFor(catalog.provider, catalog.models || []);
    const resolvedModel = catalog.provider === "disabled" ? "none" : nextModel;
    const nextCustomModel = resolvedModel !== "none" && !ids.includes(resolvedModel) ? resolvedModel : "";
    setCustomModel(nextCustomModel);

    if (updateSelectedModel) {
      setForm((current) => ({
        ...current,
        selected_model: resolvedModel
      }));
    }
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
      selected_model: provider === "disabled" ? "none" : "custom-model",
      base_url: DEFAULT_BASE_URLS[provider] ?? current.base_url
    }));
    setCustomModel("");
    setModelCatalog(null);
    loadModelCatalog(provider, null, true);
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

  function updateModelSelection(event) {
    const value = event.target.value;
    if (value === CUSTOM_MODEL_VALUE) {
      const existingCustomModel =
        form.selected_model !== "none" && !modelIds.includes(form.selected_model) ? form.selected_model : "";
      const nextCustomModel = customModel || existingCustomModel || "custom-model";
      setCustomModel(nextCustomModel);
      setForm((current) => ({
        ...current,
        selected_model: nextCustomModel
      }));
      return;
    }
    setCustomModel("");
    setForm((current) => ({
      ...current,
      selected_model: value
    }));
  }

  function updateCustomModel(event) {
    const value = event.target.value;
    setCustomModel(value);
    setForm((current) => ({
      ...current,
      selected_model: value
    }));
  }

  function buildPayload(includeApiKey) {
    const payload = {
      ...form,
      selected_model: form.llm_provider === "disabled" ? "none" : form.selected_model || "custom-model",
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

  async function refreshModels() {
    setModelsRefreshing(true);
    setError("");
    setMessage("");
    try {
      const response = await refreshLlmModels(form.llm_provider);
      applyModelCatalog(response, form.selected_model, false);
      setMessage(response.message);
    } catch (err) {
      setError(err.message);
    } finally {
      setModelsRefreshing(false);
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

      <Card className="appearance-card">
        <div className="card-row">
          <div>
            <h3>{t("appearance.title")}</h3>
            <p className="muted">
              {t("appearance.subtitle")}{" "}
              <strong>
                {resolvedTheme === "dark" ? t("appearance.currentlyDark") : t("appearance.currentlyLight")}
              </strong>
            </p>
          </div>
          <Badge tone="neutral">{resolvedTheme === "dark" ? t("appearance.dark") : t("appearance.light")}</Badge>
        </div>
        <div className="appearance-options" role="radiogroup" aria-label={t("appearance.title")}>
          {APPEARANCE_OPTIONS.map((option) => {
            const label = t(`appearance.${option}`);
            const description =
              option === "system"
                ? t("appearance.followSystem", {
                    current: systemPrefersDark ? t("appearance.currentlyDark") : t("appearance.currentlyLight")
                  })
                : t(`appearance.${option}Description`);
            return (
              <label key={option} className={`appearance-option ${appearancePreference === option ? "is-selected" : ""}`}>
                <input
                  type="radio"
                  name="appearance"
                  value={option}
                  checked={appearancePreference === option}
                  onChange={() => setAppearancePreference(option)}
                />
                <span>
                  <strong>{label}</strong>
                  <small>{description}</small>
                </span>
              </label>
            );
          })}
        </div>
      </Card>

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
                  name="selected_model_choice"
                  value={modelSelectValue}
                  onChange={updateModelSelection}
                  disabled={providerIsDisabled || modelsLoading}
                >
                  {providerIsDisabled && <option value="none">none</option>}
                  {modelOptions.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name || model.id}
                    </option>
                  ))}
                  {!providerIsDisabled && <option value={CUSTOM_MODEL_VALUE}>{t("settings.customModelOption")}</option>}
                </select>
              </label>

              {showCustomModel && (
                <label>
                  {t("settings.customModelId")}
                  <input
                    name="selected_model"
                    value={customModel}
                    onChange={updateCustomModel}
                    placeholder={t("settings.customModelPlaceholder")}
                  />
                </label>
              )}

              <div className="form-actions model-refresh-actions">
                <Button type="button" onClick={refreshModels} disabled={modelsRefreshing || modelsLoading || providerIsDisabled}>
                  {modelsRefreshing ? t("settings.refreshingModels") : t("settings.refreshModels")}
                </Button>
              </div>

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

            <div className="model-catalog-status">
              <div className="card-row">
                <strong>{t("settings.modelCatalog")}</strong>
                <Badge tone={statusTone(modelCatalog?.status)}>{modelCatalog?.status || (modelsLoading ? "loading" : "unknown")}</Badge>
              </div>
              <p>
                {t("settings.modelSource")}: {modelCatalog?.source || "unknown"}
                {modelCatalog?.fetched_at ? ` · ${t("settings.fetchedAt")}: ${modelCatalog.fetched_at}` : ""}
              </p>
              <p>{modelsLoading ? t("common.loading") : modelCatalog?.message || t("settings.modelCatalogHelp")}</p>
            </div>

            <p className="muted">{t("settings.keyStorageHelp")}</p>
            <p className="muted">{t("settings.modelCatalogHelp")}</p>
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

        <Card>
          <div className="card-row">
            <h3>{t("settings.financialData")}</h3>
            <Badge tone={financialStatusTone(financialStatus?.availability_status)}>
              {financialStatus?.availability_status || "unknown"}
            </Badge>
          </div>
          <p className="muted">{t("settings.financialDataHelp")}</p>
          <dl className="detail-list">
            <div>
              <dt>{t("settings.activeProvider")}</dt>
              <dd>{financialStatus?.provider || "unknown"}</dd>
            </div>
            <div>
              <dt>{t("research.freshness")}</dt>
              <dd>{financialStatus?.freshness_status || "unknown"}</dd>
            </div>
            <div>
              <dt>{t("settings.cacheEntries")}</dt>
              <dd>{financialStatus?.cache?.entries ?? 0}</dd>
            </div>
            <div>
              <dt>{t("settings.providerConfiguration")}</dt>
              <dd>{financialStatus?.configuration?.provider_selection || "backend environment only"}</dd>
            </div>
          </dl>
          <div className="evidence-chip-row">
            {(financialStatus?.capabilities || []).map((capability) => (
              <span className="evidence-chip" key={capability}>{capability}</span>
            ))}
          </div>
          {(financialStatus?.warnings || []).length > 0 && (
            <div className="warning-list">
              {(financialStatus?.warnings || []).map((warning) => (
                <p key={warning} className="data-disclaimer">{warning}</p>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <div className="card-row">
            <h3>{t("settings.newsResearch")}</h3>
            <Badge tone={newsResearchStatus?.enabled ? "success" : "warning"}>
              {newsResearchStatus?.enabled ? t("settings.enabled") : t("settings.disabled")}
            </Badge>
          </div>
          <p className="muted">{t("settings.newsResearchHelp")}</p>
          <dl className="detail-list">
            <div>
              <dt>{t("settings.activeProvider")}</dt>
              <dd>{newsResearchStatus?.provider || "unknown"}</dd>
            </div>
            <div>
              <dt>{t("settings.liveNewsSupport")}</dt>
              <dd>{newsResearchStatus?.supports_live_news ? t("llm.yes") : t("llm.no")}</dd>
            </div>
            <div>
              <dt>{t("settings.sentimentSupport")}</dt>
              <dd>{newsResearchStatus?.supports_sentiment ? t("llm.yes") : t("llm.no")}</dd>
            </div>
            <div>
              <dt>{t("settings.cacheStatus")}</dt>
              <dd>{newsResearchStatus?.cache_status?.enabled ? t("settings.enabled") : t("settings.disabled")}</dd>
            </div>
          </dl>
          {[
            ...(newsResearchStatus?.warnings || []),
            ...(newsResearchStatus?.unavailable_reasons || [])
          ].length > 0 && (
            <div className="warning-list">
              {[...new Set([...(newsResearchStatus?.warnings || []), ...(newsResearchStatus?.unavailable_reasons || [])])].map((warning) => (
                <p key={warning} className="data-disclaimer">{warning}</p>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

function financialStatusTone(status) {
  if (status === "available") return "success";
  if (status === "partial" || status === "stale_cache") return "warning";
  if (status === "failed" || status === "unavailable" || status === "unsupported") return "danger";
  return "neutral";
}
