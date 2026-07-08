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
