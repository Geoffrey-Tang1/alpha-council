const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error?.detail || error?.error?.message || `Request failed: ${response.status}`);
  }

  return response.json();
}

export function getHealth() {
  return request("/health");
}

export function getMarketStatus() {
  return request("/market-status");
}

export function runAnalysis(payload) {
  return request("/analysis/run", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getDecisions() {
  return request("/decisions");
}
