import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import ja from "./locales/ja.json";
import ko from "./locales/ko.json";
import zhTW from "./locales/zh-TW.json";

export const SUPPORTED_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "zh-TW", label: "繁體中文" },
  { code: "ja", label: "日本語" },
  { code: "ko", label: "한국어" }
];

const LANGUAGE_STORAGE_KEY = "alphacouncil.language";
const fallbackLanguage = "en";

function getInitialLanguage() {
  if (typeof window === "undefined") {
    return fallbackLanguage;
  }

  const savedLanguage = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (SUPPORTED_LANGUAGES.some((language) => language.code === savedLanguage)) {
    return savedLanguage;
  }

  const browserLanguage = window.navigator.language;
  if (SUPPORTED_LANGUAGES.some((language) => language.code === browserLanguage)) {
    return browserLanguage;
  }

  const baseLanguage = browserLanguage.split("-")[0];
  if (baseLanguage === "zh") {
    return "zh-TW";
  }
  const supportedBaseLanguage = SUPPORTED_LANGUAGES.find((language) => language.code === baseLanguage);
  return supportedBaseLanguage?.code || fallbackLanguage;
}

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    "zh-TW": { translation: zhTW },
    ja: { translation: ja },
    ko: { translation: ko }
  },
  lng: getInitialLanguage(),
  fallbackLng: fallbackLanguage,
  interpolation: {
    escapeValue: false
  },
  returnEmptyString: false
});

i18n.on("languageChanged", (language) => {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  }
});

export default i18n;
