import { useTranslation } from "react-i18next";

import Badge from "../ui/Badge.jsx";
import Card from "../ui/Card.jsx";

function providerLabel(t, provider) {
  if (provider === "mock") return t("llm.mockLlm");
  if (provider === "openai") return t("llm.openai");
  if (provider === "anthropic") return t("llm.anthropic");
  if (provider === "gemini") return t("settings.providers.gemini");
  if (provider === "deepseek") return t("settings.providers.deepseek");
  if (provider === "xai") return t("settings.providers.xai");
  if (provider === "mistral") return t("settings.providers.mistral");
  if (provider === "groq") return t("settings.providers.groq");
  if (provider === "openrouter") return t("settings.providers.openrouter");
  if (provider === "ollama") return t("settings.providers.ollama");
  if (provider === "custom_openai_compatible") return t("settings.providers.custom_openai_compatible");
  return t("llm.disabled");
}

function providerTone(provider, enabled, used) {
  if (!enabled || !used) return "neutral";
  if (provider === "mock") return "warning";
  return "success";
}

function LLMOutputSection({ title, output }) {
  const { t } = useTranslation();

  if (!output?.summary) {
    return null;
  }

  return (
    <section className="llm-output-section">
      <h4>{title}</h4>
      <p>{output.summary}</p>
      {output.reasoning_notes?.length > 0 && (
        <details>
          <summary>{t("llm.reasoningNotes")}</summary>
          <ul className="stack-list">
            {output.reasoning_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

export default function LLMResearchMemo({ decision }) {
  const { t } = useTranslation();

  if (!decision) {
    return null;
  }

  const outputs = decision.llm_outputs || {};
  const promptVersions = Object.entries(outputs.prompt_versions || {});
  const hasMemo = Boolean(
    outputs.decision_memo?.summary ||
      outputs.risk_explanation?.summary ||
      outputs.bull_bear_summary?.summary ||
      outputs.research_report?.summary
  );

  return (
    <Card className="llm-memo-card">
      <div className="card-row">
        <div>
          <p className="eyebrow">{t("llm.status")}</p>
          <h3>{t("llm.title")}</h3>
          <p className="muted">
            {t("llm.used")}: {decision.llm_used ? t("llm.yes") : t("llm.no")}
          </p>
          <p className="muted">
            {t("settings.provider")}: {providerLabel(t, decision.llm_provider)} · {t("settings.model")}:{" "}
            {decision.llm_model || outputs.decision_memo?.model || "none"}
          </p>
        </div>
        <div className="decision-badges">
          <Badge tone={providerTone(decision.llm_provider, decision.llm_enabled, decision.llm_used)}>
            {providerLabel(t, decision.llm_provider)}
          </Badge>
        </div>
      </div>

      {decision.llm_warnings?.length > 0 && (
        <div>
          <h4>{t("llm.warnings")}</h4>
          <ul className="stack-list warning-list">
            {decision.llm_warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {!hasMemo && <p className="muted">{t("llm.noMemo")}</p>}

      <div className="llm-memo-grid">
        <LLMOutputSection title={t("llm.decisionMemo")} output={outputs.decision_memo} />
        <LLMOutputSection title={t("llm.riskExplanation")} output={outputs.risk_explanation} />
        <LLMOutputSection title={t("llm.bullBearSummary")} output={outputs.bull_bear_summary} />
        <LLMOutputSection title={t("llm.researchReport")} output={outputs.research_report} />
      </div>

      {promptVersions.length > 0 && (
        <details className="llm-prompt-metadata">
          <summary>{t("llm.promptMetadata")}</summary>
          <dl className="detail-list">
            {promptVersions.map(([promptName, version]) => (
              <div key={promptName}>
                <dt>{promptName}</dt>
                <dd>{version}</dd>
              </div>
            ))}
          </dl>
        </details>
      )}
    </Card>
  );
}
