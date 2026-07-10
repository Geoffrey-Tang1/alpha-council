import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  DEFAULT_APPEARANCE,
  applyResolvedTheme,
  getSystemPrefersDark,
  normalizeAppearancePreference,
  readStoredAppearancePreference,
  resolveAppearancePreference,
  writeStoredAppearancePreference
} from "./appearance.js";

const ThemeContext = createContext({
  appearancePreference: DEFAULT_APPEARANCE,
  resolvedTheme: "dark",
  systemPrefersDark: true,
  setAppearancePreference: () => {}
});

export function ThemeProvider({ children }) {
  const [appearancePreference, setAppearancePreferenceState] = useState(readStoredAppearancePreference);
  const [systemPrefersDark, setSystemPrefersDark] = useState(getSystemPrefersDark);

  const resolvedTheme = resolveAppearancePreference(appearancePreference, systemPrefersDark);

  useEffect(() => {
    applyResolvedTheme(resolvedTheme);
  }, [resolvedTheme]);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return undefined;
    }

    const query = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = (event) => {
      setSystemPrefersDark(event.matches);
    };

    if (typeof query.addEventListener === "function") {
      query.addEventListener("change", handleChange);
      return () => query.removeEventListener("change", handleChange);
    }

    query.addListener(handleChange);
    return () => query.removeListener(handleChange);
  }, []);

  function setAppearancePreference(nextPreference) {
    const normalized = normalizeAppearancePreference(nextPreference);
    writeStoredAppearancePreference(normalized);
    setAppearancePreferenceState(normalized);
  }

  const value = useMemo(
    () => ({
      appearancePreference,
      resolvedTheme,
      systemPrefersDark,
      setAppearancePreference
    }),
    [appearancePreference, resolvedTheme, systemPrefersDark]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  return useContext(ThemeContext);
}
