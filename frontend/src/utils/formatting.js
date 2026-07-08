export function formatPrice(value) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  }).format(value);
}

export function formatConfidence(value) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return `${Math.round(value * 100)}%`;
}

export function formatPercent(value) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return `${(value * 100).toFixed(2)}%`;
}

export function formatCurrency(value) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(value);
}

export function formatDateTime(value) {
  if (!value) {
    return "N/A";
  }
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatTimestampCompact(value) {
  if (!value) {
    return "N/A";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "N/A";
  }
  const parts = new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).formatToParts(date);
  const pick = (type) => parts.find((part) => part.type === type)?.value || "";
  return `${pick("year")}-${pick("month")}-${pick("day")} ${pick("hour")}:${pick("minute")}`;
}

export function formatInstrument(companyName, displaySymbol, fallbackTicker) {
  const safeCompany = companyName || "Unknown Company";
  const safeSymbol = displaySymbol || fallbackTicker || "N/A";
  return `${safeCompany} (${safeSymbol})`;
}

export const MARKET_DISPLAY = {
  US: {
    country: "United States",
    city: "New York",
    timezoneLabel: "US Eastern Time"
  },
  JP: {
    country: "Japan",
    city: "Tokyo",
    timezoneLabel: "Japan Standard Time"
  },
  TW: {
    country: "Taiwan",
    city: "Taipei",
    timezoneLabel: "Taiwan Time"
  },
  KR: {
    country: "Korea",
    city: "Seoul",
    timezoneLabel: "Korea Standard Time"
  }
};

const TIMEZONE_LABELS = {
  "America/New_York": MARKET_DISPLAY.US.timezoneLabel,
  "Asia/Tokyo": MARKET_DISPLAY.JP.timezoneLabel,
  "Asia/Taipei": MARKET_DISPLAY.TW.timezoneLabel,
  "Asia/Seoul": MARKET_DISPLAY.KR.timezoneLabel
};

export function getMarketDisplay(marketCode, fallbackTimezone) {
  const display = MARKET_DISPLAY[marketCode] || {};
  return {
    country: display.country || marketCode || "Unknown Market",
    city: display.city || "Local market",
    timezoneLabel: display.timezoneLabel || formatTimezoneLabel(fallbackTimezone)
  };
}

export function formatTimezoneLabel(timezone) {
  return TIMEZONE_LABELS[timezone] || "Local time";
}

export function formatMarketLocalTime(timezone, now = new Date(), locale = "en-US") {
  if (!timezone) {
    return "Local time unavailable";
  }
  try {
    return new Intl.DateTimeFormat(locale, {
      timeZone: timezone,
      hour: "2-digit",
      minute: "2-digit",
      hour12: true
    }).format(now);
  } catch {
    return "Local time unavailable";
  }
}

export function truncateText(text, maxLength = 140) {
  if (!text) {
    return "";
  }
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1).trim()}…`;
}
