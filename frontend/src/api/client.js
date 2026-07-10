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

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function getHealth() {
  return request("/health");
}

export function getMarketStatus() {
  return request("/market-status");
}

export function getDataSourceStatus() {
  return request("/data-sources/status");
}

export function getLLMStatus() {
  return request("/llm/status");
}

export function getLlmStatus() {
  return getLLMStatus();
}

export function getLlmSettings() {
  return request("/llm/settings");
}

export function getLlmModels(provider) {
  const query = new URLSearchParams({ provider });
  return request(`/llm/models?${query.toString()}`);
}

export function refreshLlmModels(provider) {
  return request("/llm/models/refresh", {
    method: "POST",
    body: JSON.stringify({ provider })
  });
}

export function updateLlmSettings(payload) {
  return request("/llm/settings", {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function testLlmConnection(payload) {
  return request("/llm/test", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getWatchlist() {
  return request("/watchlist");
}

export function getWatchlistSummary() {
  return request("/watchlist/summary");
}

export function addWatchlistItem(payload) {
  return request("/watchlist", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateWatchlistItem(id, payload) {
  return request(`/watchlist/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function deleteWatchlistItem(id) {
  return request(`/watchlist/${id}`, {
    method: "DELETE"
  });
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

export function getDecision(decisionId) {
  return request(`/decisions/${decisionId}`);
}

export function runBacktest(payload) {
  return request("/backtests/run", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getBacktests() {
  return request("/backtests");
}

export function getBacktest(backtestId) {
  return request(`/backtests/${backtestId}`);
}

export function runEvaluation(payload) {
  return request("/evaluations/run", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function evaluateDecision(decisionId) {
  return request(`/evaluations/decision/${decisionId}`, {
    method: "POST"
  });
}

export function getEvaluations(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/evaluations${suffix}`);
}

export function getEvaluation(evaluationId) {
  return request(`/evaluations/${evaluationId}`);
}

export function getEvaluationSummary() {
  return request("/evaluations/summary");
}
