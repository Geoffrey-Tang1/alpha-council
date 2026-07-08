export function enumLabel(t, value) {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }
  return t(`enums.${value}`, { defaultValue: String(value) });
}

export function strategyLabel(t, value) {
  if (!value) {
    return "N/A";
  }
  return t(`strategies.${value}`, { defaultValue: value });
}
