import { useTranslation } from "react-i18next";

import { SUPPORTED_LANGUAGES } from "../../i18n/index.js";

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation();

  function changeLanguage(event) {
    i18n.changeLanguage(event.target.value);
  }

  return (
    <label className="language-switcher">
      <span>{t("language.label")}</span>
      <select value={i18n.resolvedLanguage || i18n.language} onChange={changeLanguage}>
        {SUPPORTED_LANGUAGES.map((language) => (
          <option key={language.code} value={language.code}>
            {language.label}
          </option>
        ))}
      </select>
    </label>
  );
}
