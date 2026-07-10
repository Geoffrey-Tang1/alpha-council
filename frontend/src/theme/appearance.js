export const APPEARANCE_STORAGE_KEY = "wisoka.appearance";
export const APPEARANCE_OPTIONS = ["dark", "light", "system"];
export const DEFAULT_APPEARANCE = "dark";

const DARK_THEME_COLOR = "#07111F";
const LIGHT_THEME_COLOR = "#F4F8FC";

export function normalizeAppearancePreference(value) {
  return APPEARANCE_OPTIONS.includes(value) ? value : DEFAULT_APPEARANCE;
}

export function getSystemPrefersDark() {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return true;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function resolveAppearancePreference(preference, systemPrefersDark = getSystemPrefersDark()) {
  const normalized = normalizeAppearancePreference(preference);
  if (normalized === "system") {
    return systemPrefersDark ? "dark" : "light";
  }
  return normalized;
}

export function readStoredAppearancePreference() {
  if (typeof window === "undefined") {
    return DEFAULT_APPEARANCE;
  }

  try {
    return normalizeAppearancePreference(window.localStorage.getItem(APPEARANCE_STORAGE_KEY));
  } catch {
    return DEFAULT_APPEARANCE;
  }
}

export function writeStoredAppearancePreference(preference) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(APPEARANCE_STORAGE_KEY, normalizeAppearancePreference(preference));
  } catch {
    // Local storage can be unavailable in private or restricted browser contexts.
  }
}

export function applyResolvedTheme(resolvedTheme) {
  if (typeof document === "undefined") {
    return;
  }

  const theme = resolvedTheme === "light" ? "light" : "dark";
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;

  const themeColor = theme === "light" ? LIGHT_THEME_COLOR : DARK_THEME_COLOR;
  let metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (!metaThemeColor) {
    metaThemeColor = document.createElement("meta");
    metaThemeColor.setAttribute("name", "theme-color");
    document.head.appendChild(metaThemeColor);
  }
  metaThemeColor.setAttribute("content", themeColor);
}
